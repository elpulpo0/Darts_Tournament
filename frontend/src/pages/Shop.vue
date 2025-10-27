<template>
  <div v-if="authStore.isAuthenticated" class="module shop-page">
    <header class="shop-header">
      <h1>Boutique Badarts</h1>
      <p>Nos t-shirts, maillots et casquettes personnalisés. Fabriqués sur demande – commande et soutiens le club !
      </p>
    </header>
    <div v-if="loading" class="loading">Chargement des produits...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="products.length === 0" class="no-products">Aucun produit disponible</div>
    <div v-else class="products-grid">
      <div v-for="(product, index) in products" class="product-card" :key="product.id">
        <img :src="getMainImage(product, selectedVariants[index])" :alt="product.name" loading="lazy"
          class="product-image" />
        <h3>{{ product.name }}</h3>
        <p class="price">Prix TTC : {{ getCurrentPrice(product, selectedVariants[index]) }}€</p>
        <div v-if="hasVariants(product)" class="variants-selector">
          <div v-if="product.name.includes('Casquette')" class="color-selector">
            <span class="variant-label">Couleur :</span>
            <ul class="variants">
              <li v-for="variant in product.sync_variants"
                :class="{ selected: selectedVariants[index]?.id === variant.id }" class="variant-color"
                :style="{ backgroundColor: getColorForVariant(variant.color) }" :title="variant.color"
                @click="selectVariant(index, variant)" :key="`v-${variant.id}`"></li>
            </ul>
          </div>
          <div v-else class="size-selector">
            <span class="variant-label">Taille :</span>
            <select v-model="selectedVariants[index]" @change="selectVariant(index, selectedVariants[index])">
              <option v-for="variant in product.sync_variants" :value="variant" :key="`v-${variant.id}`">
                {{ variant.size }}
              </option>
            </select>
          </div>
        </div>
        <p v-else class="no-variants">Variantes non configurées (contactez-nous !)</p>
        <button :disabled="!hasVariants(product)" @click="addToCart(product, selectedVariants[index])">
          Ajouter au panier
        </button>
      </div>
    </div>
    <div v-if="cart.length" class="cart-summary">
      <h3>Panier ({{ cart.length }} produit{{ cart.length > 1 ? 's' : '' }})</h3>
      <div class="cart-items">
        <div v-for="(item, index) in cart" class="cart-item" :key="`cart-${index}`">
          <div class="cart-item-header">
            <span v-if="item.name.includes('Casquette')" class="cart-item-name">{{ item.name }} {{
              item.selectedVariant.color }}</span>
            <span v-else class="cart-item-name">{{ item.name }} (Taille {{ item.selectedVariant.size }})</span>
            <button class="remove-button" @click="removeFromCart(index)">&times;</button>
          </div>
        </div>
      </div>
      <p class="cart-total">Total TTC : {{ cartTotal }} EUR</p>
      <button :disabled="costLoading" @click="openCheckoutForm">Valider le panier</button>
    </div>
    <div v-if="showCheckout" class="checkout-form">
      <h3>Informations de livraison</h3>
      <div v-if="error" class="error">{{ error }}</div>
      <form @submit.prevent="proceedToPayment">
        <input v-model="orderForm.name" placeholder="Nom complet" required class="input-field" />
        <input v-model="orderForm.email" type="email" placeholder="Email" required class="input-field" />
        <input v-model="orderForm.address" placeholder="Adresse (rue, numéro)" required class="input-field" />
        <input v-model="orderForm.address2" placeholder="Complément d'adresse (optionnel)" class="input-field" />
        <input v-model="orderForm.city" placeholder="Ville" required class="input-field" />
        <input v-model="orderForm.zip" placeholder="Code postal" required class="input-field" />
        <input v-model="orderForm.phone" placeholder="Téléphone (optionnel)" class="input-field" />
        <div class="form-buttons">
          <button type="submit" :disabled="costLoading || paymentLoading">Valider</button>
          <button type="button" :disabled="costLoading || paymentLoading" @click="showCheckout = false">Annuler</button>
        </div>
      </form>
    </div>
    <div v-if="showPayment" class="payment-section">
      <h3>Paiement</h3>
      <div v-if="costBreakdown.subtotal" class="cost-breakdown">
        <p>Sous-total : {{ costBreakdown.subtotal }} EUR</p>
        <p>Frais de livraison : {{ costBreakdown.shipping }} EUR</p>
        <p class="cart-total">Total TTC : {{ costBreakdown.total }} EUR</p>
      </div>
      <p v-else-if="costLoading" class="loading">Calcul des frais en cours...</p>
      <p v-else class="error">Erreur lors du calcul des frais. Veuillez réessayer.</p>
      <div v-if="!costLoading && costBreakdown.total && draftOrderId" id="paypal-button-container"></div>
      <p v-if="paymentLoading" class="loading">Paiement en cours...</p>
      <div class="form-buttons">
        <button type="button" :disabled="paymentLoading || costLoading"
          @click="showPayment = false; showCheckout = true">
          Retour
        </button>
      </div>
    </div>
    <div v-if="orderDetails.id" class="order-confirmation">
      <h3>Commande confirmée !</h3>
      <p>Numéro de commande : {{ orderDetails.id }}</p>
      <p>Total payé TTC : {{ orderDetails.total }} {{ orderDetails.currency }}</p>
      <p>Merci pour votre paiement ! Votre transaction est terminée et votre commande sera traitée dans les plus brefs
        délais.</p>
    </div>
    <router-link to="/home" class="back-link">← Retour à l'accueil</router-link>
  </div>

  <div v-else class="centered-block">
    <h2>🔒 Connexion requise</h2>
    <p>Veuillez vous connecter pour accéder à la boutique.</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { toast } from 'vue3-toastify'
import { useRoute } from 'vue-router'
import backendApi from '../axios/backendApi'
import { useAuthStore } from '../stores/useAuthStore'

// PayPal type definitions
interface PayPalOrder {
  order: {
    create: (config: {
      payer?: {
        name?: { given_name: string; surname: string }
        email_address?: string
        phone?: { phone_number: { national_number: string }; country_code: string }
        address?: {
          address_line_1: string
          address_line_2?: string
          admin_area_2: string
          postal_code: string
          country_code: string
        }
      }
      purchase_units: Array<{
        amount: {
          value: string
          currency_code: string
          breakdown?: {
            item_total?: { value: string; currency_code: string }
            shipping?: { value: string; currency_code: string }
          }
        }
        custom_id?: string
        shipping?: {
          name?: { full_name: string }
          address: {
            address_line_1: string
            address_line_2?: string
            admin_area_2: string
            postal_code: string
            country_code: string
          }
        }
      }>
    }) => Promise<string>
    capture: () => Promise<{ purchase_units: Array<{ custom_id: string; shipping?: any }> }>
  }
}

declare global {
  interface Window {
    paypal: {
      Buttons: (config: {
        createOrder: (_data: any, actions: PayPalOrder) => Promise<string>
        onApprove: (_data: any, actions: PayPalOrder) => Promise<void>
        onCancel?: () => void
        onError?: (err: any) => void
      }) => { render: (container: string) => void }
    }
  }
}

const authStore = useAuthStore()
const route = useRoute()

const products = ref<any[]>([])
const cart = ref<any[]>([])
const selectedVariants = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const showCheckout = ref(false)
const showPayment = ref(false)
const paymentLoading = ref(false)
const costLoading = ref(false)
const orderDetails = ref<any>({})
const cartTotal = ref('0.00')
const shippingCost = ref('0.00')
const draftOrderId = ref<number | null>(null)
const costBreakdown = ref({
  subtotal: '0.00',
  shipping: '0.00',
  total: '0.00'
})

const orderForm = ref({
  name: '',
  email: '',
  address: '',
  address2: '',
  city: '',
  zip: '',
  phone: ''
})

const placeholderImage = '/images/placeholder.svg'

const colorMap: Record<string, string> = {
  Black: '#262626',
  Navy: '#222942',
  Red: '#FF0024',
  Olive: '#625c43',
  'Green Tiger Camo': '#5e5f56',
  Gray: '#7b7979',
  Khaki: '#ffd096',
}

// Track if PayPal Buttons are already rendered to prevent duplicates
const isPaypalButtonsRendered = ref(false)

// Load PayPal SDK dynamically
const loadPaypalSDK = () => {
  return new Promise<void>((resolve, reject) => {
    const paypalClientId = import.meta.env.VITE_PAYPAL_CLIENT_ID as string
    if (!paypalClientId) {
      console.error('Client ID PayPal manquant dans .env')
      error.value = 'Erreur de configuration PayPal. Veuillez contacter le support.'
      reject(new Error('Missing PayPal Client ID'))
      return
    }
    if (window.paypal) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = `https://www.sandbox.paypal.com/sdk/js?client-id=${paypalClientId}&currency=EUR`
    script.async = true
    script.onload = () => {
      resolve()
    }
    script.onerror = () => {
      console.error('Erreur lors du chargement du SDK PayPal')
      error.value = 'Erreur de chargement du paiement PayPal. Veuillez réessayer.'
      reject(new Error('Failed to load PayPal SDK'))
    }
    document.head.appendChild(script)
  })
}

// Initialize PayPal Buttons
const initPaypalButtons = async () => {
  if (isPaypalButtonsRendered.value) {
    return
  }

  try {
    await loadPaypalSDK() // Ensure SDK is loaded
    if (!window.paypal) {
      console.error('PayPal SDK non chargé')
      error.value = 'Erreur de chargement du paiement PayPal.'
      return
    }
    if (costLoading.value) {
      console.error('Coût en cours de chargement')
      error.value = 'Veuillez attendre la fin du calcul des frais.'
      return
    }
    if (!costBreakdown.value.total || parseFloat(costBreakdown.value.total) <= 0) {
      console.error('Total invalide:', costBreakdown.value.total)
      error.value = 'Erreur: Montant total invalide.'
      return
    }
    if (!draftOrderId.value) {
      console.error('Draft Order ID manquant')
      error.value = 'Erreur: Commande non initialisée.'
      return
    }

    // Clear previous buttons if any
    const container = document.getElementById('paypal-button-container')
    if (container) {
      container.innerHTML = ''
    }

    window.paypal.Buttons({
      createOrder: async (_data, actions: PayPalOrder) => {
        try {
          const total = parseFloat(costBreakdown.value.total)
          const subtotal = parseFloat(costBreakdown.value.subtotal)
          const shipping = parseFloat(costBreakdown.value.shipping)
          if (isNaN(total) || total <= 0) {
            throw new Error('Montant total invalide: ' + costBreakdown.value.total)
          }
          if (isNaN(subtotal) || subtotal < 0) {
            throw new Error('Sous-total invalide: ' + costBreakdown.value.subtotal)
          }
          if (isNaN(shipping) || shipping < 0) {
            throw new Error('Frais de livraison invalides: ' + costBreakdown.value.shipping)
          }

          // Préparer l'objet d'adresse pour PayPal (utilisé pour shipping ET billing via payer)
          const payerAddress = {
            address_line_1: orderForm.value.address,
            address_line_2: orderForm.value.address2 || undefined,
            admin_area_2: orderForm.value.city,
            postal_code: orderForm.value.zip,
            country_code: 'FR'
          }

          // Préparer l'objet payer, en incluant le téléphone uniquement si valide
          const payer: any = {
            name: {
              given_name: orderForm.value.name.split(' ')[0] || 'Prénom', // Premier prénom
              surname: orderForm.value.name.split(' ').slice(1).join(' ') || 'Nom' // Reste du nom
            },
            email_address: orderForm.value.email || 'email@example.com',
            address: payerAddress // Adresse de facturation (préremplit le formulaire carte)
          }

          // Valider et formater le numéro de téléphone (si fourni)
          const phoneNumber = orderForm.value.phone?.replace(/\D/g, '') // Nettoyer les caractères non numériques
          if (phoneNumber && phoneNumber.length >= 9 && phoneNumber.length <= 15) {
            payer.phone = {
              phone_number: {
                national_number: phoneNumber
              },
              country_code: '33' // Code pays France
            }
          }

          return actions.order.create({
            payer, // Inclure l'objet payer avec ou sans téléphone
            purchase_units: [{
              amount: {
                value: total.toFixed(2),
                currency_code: 'EUR',
                breakdown: {
                  item_total: { value: subtotal.toFixed(2), currency_code: 'EUR' },
                  shipping: { value: shipping.toFixed(2), currency_code: 'EUR' }
                }
              },
              custom_id: 'PF' + draftOrderId.value,
              shipping: {
                name: {
                  full_name: orderForm.value.name || 'Test Name'
                },
                address: payerAddress // Réutiliser pour shipping (cohérent avec Printful)
              }
            }]
          })
        } catch (err: any) {
          console.error('Erreur dans createOrder:', err)
          error.value = 'Erreur lors de la création du paiement: ' + (err.message || 'Erreur inconnue.')
          throw err
        }
      },
      onApprove: async (_data, actions: PayPalOrder) => {
        paymentLoading.value = true
        try {
          const order = await actions.order.capture()
          const customId = order.purchase_units[0].custom_id
          if (!customId || !customId.startsWith('PF')) {
            throw new Error('custom_id invalide ou manquant: ' + customId)
          }
          const orderId = customId.replace('PF', '')
          orderDetails.value = {
            id: orderId,
            total: costBreakdown.value.total,
            currency: 'EUR'
          }
          toast.success('Paiement reçu ! Votre commande est en cours de traitement.')
          // Reset state after successful payment
          error.value = ''
          cart.value = []
          costBreakdown.value = { subtotal: '0.00', shipping: '0.00', total: '0.00' }
          cartTotal.value = '0.00'
          shippingCost.value = '0.00'
          paymentLoading.value = false
          draftOrderId.value = null
          showPayment.value = false
          showCheckout.value = false
          isPaypalButtonsRendered.value = false
        } catch (err: any) {
          console.error('PayPal capture error:', err)
          error.value = 'Erreur lors de la capture du paiement: ' + (err.message || 'Erreur inconnue.')
          paymentLoading.value = false
        }
      },
      onCancel: () => {
        error.value = 'Paiement annulé. Veuillez réessayer.'
        paymentLoading.value = false
        isPaypalButtonsRendered.value = false
      },
      onError: (err: any) => {
        console.error('PayPal error:', err)
        error.value = err.message?.includes('EWP_SETTINGS')
          ? 'Erreur de configuration PayPal. Contactez le support.'
          : 'Erreur lors du paiement: ' + (err.message || 'Erreur inconnue.')
        paymentLoading.value = false
        isPaypalButtonsRendered.value = false
      }
    }).render('#paypal-button-container')
    isPaypalButtonsRendered.value = true
  } catch (err: any) {
    console.error('Erreur initPaypalButtons:', err)
    error.value = 'Erreur de configuration du paiement PayPal: ' + (err.message || 'Erreur inconnue.')
  }
}

onMounted(async () => {
  if (authStore.name) orderForm.value.name = authStore.name
  if (authStore.email) orderForm.value.email = authStore.email
  try {
    const summaryResponse = await backendApi.get('/api/printful/store/products')
    const summaries = summaryResponse.data.result.slice(0, 3)

    if (summaries.length === 0) {
      error.value = 'Aucun produit trouvé'
      loading.value = false
      return
    }

    const fullProducts = await Promise.all(
      summaries.map(async (summary: any) => {
        const detailResponse = await backendApi.get(`/api/printful/store/products/${summary.id}`)
        return {
          ...detailResponse.data.result,
          id: summary.id,
          name: summary.name,
          thumbnail_url: summary.thumbnail_url,
        }
      })
    )

    products.value = fullProducts
    selectedVariants.value = fullProducts.map(product => product.sync_variants[0] || null)
    loading.value = false
  } catch (err: any) {
    console.error('Erreur chargement produits:', err)
    error.value = 'Erreur de chargement des produits'
    loading.value = false
  }

  // Load PayPal SDK separately to avoid blocking product loading
  try {
    await loadPaypalSDK()
  } catch (err: any) {
    console.error('Erreur chargement SDK PayPal:', err)
    error.value = 'Erreur de chargement du paiement PayPal.'
  }

  // Handle PayPal redirect
  if (route.query.payment === 'success') {
    try {
      const customData = route.query.custom as string
      if (customData && route.query.txn_id && customData.startsWith('PF')) {
        const orderId = customData.replace('PF', '')
        paymentLoading.value = true
        orderDetails.value = {
          id: orderId,
          total: costBreakdown.value.total,
          currency: 'EUR'
        }
        toast.success('Paiement reçu ! Votre commande est en cours de traitement.')
        // Reset state after successful redirect
        error.value = ''
        cart.value = []
        costBreakdown.value = { subtotal: '0.00', shipping: '0.00', total: '0.00' }
        cartTotal.value = '0.00'
        shippingCost.value = '0.00'
        paymentLoading.value = false
        draftOrderId.value = null
        showPayment.value = false
        showCheckout.value = false
      } else {
        console.error('customData invalide ou manquant:', customData)
        error.value = 'Erreur lors de la confirmation du paiement.'
      }
    } catch (err: any) {
      console.error('Erreur parsing custom_id redirect:', err)
      error.value = 'Erreur lors de la confirmation du paiement: ' + (err.message || 'Erreur inconnue.')
    }
  } else if (route.query.payment === 'cancel') {
    error.value = 'Paiement annulé. Veuillez réessayer.'
    paymentLoading.value = false
  }
})

const calculateCartTotal = () => {
  const itemTotal = cart.value.reduce((sum, item) => {
    return sum + (parseFloat(item.selectedVariant.retail_price || '0') * item.quantity)
  }, 0)
  costBreakdown.value = {
    subtotal: itemTotal.toFixed(2),
    shipping: '0.00',
    total: itemTotal.toFixed(2)
  }
  cartTotal.value = costBreakdown.value.total
  shippingCost.value = '0.00'
}

const fetchOrderCosts = async () => {
  costLoading.value = true
  draftOrderId.value = null

  if (cart.value.length > 0 && orderForm.value.address && orderForm.value.city && orderForm.value.zip) {
    try {
      const orderData = {
        recipient: {
          name: orderForm.value.name || 'Test Name',
          email: orderForm.value.email || 'test@example.com',
          address1: orderForm.value.address,
          ddress2: orderForm.value.address2 || undefined,
          city: orderForm.value.city,
          zip: orderForm.value.zip,
          country_code: 'FR',
          phone: orderForm.value.phone || undefined
        },
        items: cart.value.map((item: any) => ({
          sync_variant_id: item.selectedVariant.id,
          quantity: item.quantity
        }))
      }
      const orderResponse = await backendApi.post('/api/printful/orders', orderData)
      draftOrderId.value = orderResponse.data.result.id
      const retailCosts = orderResponse.data.result.retail_costs
      const itemTotal = parseFloat(retailCosts.subtotal) || 0
      const shipping = parseFloat(retailCosts.shipping) || 0
      if (itemTotal <= 0) {
        throw new Error('Sous-total invalide reçu de Printful: ' + itemTotal)
      }
      costBreakdown.value = {
        subtotal: itemTotal.toFixed(2),
        shipping: shipping.toFixed(2),
        total: (itemTotal + shipping).toFixed(2)
      }
      // Ne pas mettre à jour cartTotal ici pour exclure les frais de port
      shippingCost.value = costBreakdown.value.shipping
    } catch (err: any) {
      console.error('Erreur calcul des frais:', err.response?.data || err)
      error.value = err.response?.data?.detail || 'Erreur lors du calcul des frais. Veuillez réessayer.'
      costBreakdown.value = { subtotal: '0.00', shipping: '0.00', total: '0.00' }
      draftOrderId.value = null
    }
  } else {
    error.value = 'Panier vide ou informations de livraison incomplètes.'
  }
  costLoading.value = false
}

const removeFromCart = (index: number) => {
  cart.value.splice(index, 1)
  calculateCartTotal()
}

const hasVariants = (product: any) => {
  return product.sync_variants && Array.isArray(product.sync_variants) && product.sync_variants.length > 0
}

const selectVariant = (productIndex: number, variant: any) => {
  selectedVariants.value[productIndex] = variant
}

const getColorForVariant = (color: string) => {
  return colorMap[color] || '#CCCCCC'
}

const getMainImage = (product: any, selectedVariant: any = null) => {
  if (selectedVariant && product.name.includes('Casquette')) {
    const previewFile = selectedVariant.files.find((file: any) => file.type === 'preview')
    return previewFile?.preview_url || product.thumbnail_url || placeholderImage
  }
  return product.thumbnail_url || placeholderImage
}

const getCurrentPrice = (product: any, selectedVariant: any = null) => {
  if (selectedVariant?.retail_price) {
    return parseFloat(selectedVariant.retail_price).toFixed(2) // Prix TTC
  }
  if (hasVariants(product)) {
    const prices = product.sync_variants.map((v: any) => parseFloat(v.retail_price || 0))
    return Math.min(...prices).toFixed(2) // Prix TTC
  }
  return 'Prix à définir'
}

const addToCart = (product: any, selectedVariant: any = null) => {
  if (!hasVariants(product) || !selectedVariant) return
  cart.value.push({ ...product, selectedVariant, quantity: 1 })
  calculateCartTotal()
}

const openCheckoutForm = () => {
  showCheckout.value = true
  showPayment.value = false
  calculateCartTotal()
}

const proceedToPayment = async () => {
  if (!orderForm.value.name || !orderForm.value.email || !orderForm.value.address ||
    !orderForm.value.city || !orderForm.value.zip) {
    error.value = 'Veuillez remplir tous les champs obligatoires.'
    return
  }
  if (!/^\d{5}$/.test(orderForm.value.zip)) {
    error.value = 'Le code postal doit contenir exactement 5 chiffres.'
    return
  }
  if (orderForm.value.address.length < 5 || orderForm.value.city.length < 2) {
    error.value = 'Veuillez fournir une adresse et une ville valides.'
    return
  }
  await fetchOrderCosts()
  if (draftOrderId.value && costBreakdown.value.total && parseFloat(costBreakdown.value.total) > 0) {
    showCheckout.value = false
    showPayment.value = true
    await initPaypalButtons()
  } else {
    console.error('Échec préparation paiement:', { draftOrderId: draftOrderId.value, total: costBreakdown.value.total })
    error.value = 'Erreur lors de la préparation du paiement. Veuillez réessayer.'
  }
}
</script>

<style scoped>
/* Add your styles here if needed */
</style>