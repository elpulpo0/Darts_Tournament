<template>
  <div class="shop-page">
    <header class="shop-header">
      <h1>Boutique Badarts</h1>
      <p>Nos t-shirts, maillots et casquettes personnalisés. Fabriqués sur demande – commande et soutiens le club !</p>
    </header>
    <div v-if="loading" class="loading">Chargement des produits...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="products.length === 0" class="no-products">Aucun produit disponible</div>
    <div v-else class="products-grid">
      <div v-for="(product, index) in products" class="product-card" :key="product.id">
        <img :src="getMainImage(product, selectedVariants[index])" :alt="product.name" loading="lazy"
          class="product-image" />
        <h3>{{ product.name }}</h3>
        <p class="price">Prix : {{ getCurrentPrice(product, selectedVariants[index]) }}€</p>
        <div v-if="hasVariants(product)" class="variants-selector">
          <!-- Caps: Show color circles -->
          <div v-if="product.name.includes('Casquette')" class="color-selector">
            <span class="variant-label">Couleur :</span>
            <ul class="variants">
              <li v-for="variant in product.sync_variants"
                :class="{ selected: selectedVariants[index]?.id === variant.id }" class="variant-color"
                :style="{ backgroundColor: getColorForVariant(variant.color) }" :title="variant.color"
                @click="selectVariant(index, variant)" :key="`v-${variant.id}`"></li>
            </ul>
          </div>
          <!-- T-shirts: Show size selector -->
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
      <button @click="openCheckoutForm">Passer la commande</button>
    </div>
    <div v-if="showCheckout" class="checkout-form">
      <h3>Informations de livraison</h3>
      <form @submit.prevent="submitOrder">
        <input v-model="orderForm.name" placeholder="Nom complet" required class="input-field" />
        <input v-model="orderForm.email" type="email" placeholder="Email" required class="input-field" />
        <input v-model="orderForm.address" placeholder="Adresse (rue, numéro)" required class="input-field" />
        <input v-model="orderForm.city" placeholder="Ville" required class="input-field" />
        <input v-model="orderForm.zip" placeholder="Code postal" required class="input-field" />
        <input v-model="orderForm.phone" placeholder="Téléphone (optionnel)" class="input-field" />
        <div class="form-buttons">
          <!-- <button type="submit">Confirmer la commande</button> -->
          <button type="button" @click="showCheckout = false">Annuler</button>
        </div>
      </form>
    </div>
    <router-link to="/home" class="back-link">← Retour à l'accueil</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import backendApi from '../axios/backendApi'
import { useToast } from 'vue-toastification'
import { useAuthStore } from '../stores/useAuthStore'

const authStore = useAuthStore();
const toast = useToast()

const products = ref<any[]>([])
const cart = ref<any[]>([])
const selectedVariants = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const showCheckout = ref(false)

const orderForm = ref({
  name: '',
  email: '',
  address: '',
  city: '',
  zip: '',
  phone: ''
})

const placeholderImage = '/images/placeholder.svg'

const colorMap: Record<string, string> = {
  'Black': '#262626',
  'Navy': '#222942',
  'Red': '#FF0024',
  'Olive': '#625c43',
  'Green Tiger Camo': '#5e5f56',
  'Gray': '#7b7979',
  'Khaki': '#ffd096',
}

onMounted(async () => {
  if (authStore.name) {
    orderForm.value.name = authStore.name;
  }
  if (authStore.email) {
    orderForm.value.email = authStore.email;
  }
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
    // Initialize selectedVariants with the first variant of each product
    selectedVariants.value = fullProducts.map(product => product.sync_variants[0] || null)
    loading.value = false
  } catch (err: any) {
    console.error('Erreur :', err)
    error.value = 'Erreur de chargement des produits'
    loading.value = false
  }
})

const removeFromCart = (index: number) => {
  cart.value.splice(index, 1)
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
    return parseFloat(selectedVariant.retail_price).toFixed(2)
  }
  if (hasVariants(product)) {
    const prices = product.sync_variants.map((v: any) => parseFloat(v.retail_price || 0))
    return Math.min(...prices).toFixed(2)
  }
  return 'Prix à définir'
}

const addToCart = (product: any, selectedVariant: any = null) => {
  if (!hasVariants(product) || !selectedVariant) {
    return
  }
  cart.value.push({ ...product, selectedVariant, quantity: 1 })
}

const openCheckoutForm = () => {
  showCheckout.value = true
}

const submitOrder = async () => {
  // Validate form fields
  if (!orderForm.value.name || !orderForm.value.email || !orderForm.value.address ||
    !orderForm.value.city || !orderForm.value.zip) {
    error.value = 'Veuillez remplir tous les champs obligatoires.'
    return
  }

  const validCartItems = cart.value.filter(item => item.selectedVariant)
  if (validCartItems.length === 0) {
    error.value = 'Le panier est vide ou contient des articles invalides.'
    return
  }

  try {
    const orderData = {
      recipient: {
        name: orderForm.value.name,
        email: orderForm.value.email,
        address1: orderForm.value.address,
        city: orderForm.value.city,
        zip: orderForm.value.zip,
        country_code: 'FR',
        phone: orderForm.value.phone || undefined // Include phone if provided
      },
      items: validCartItems.map((item: any) => ({
        sync_variant_id: item.selectedVariant.id,
        quantity: item.quantity
      }))
    }

    const response = await backendApi.post('/api/printful/orders', orderData)
    if (response.data.result.id) {
      cart.value = []
      showCheckout.value = false
      orderForm.value = { name: '', email: '', address: '', city: '', zip: '', phone: '' }
      error.value = '' // Clear any previous errors
      toast.success('Commande passée avec succès');
    }
  } catch (err: any) {
    console.error('Erreur commande :', err)
    // Extract detailed error message from Printful API response
    const errorMessage = err.response?.data?.result || 'Erreur lors de la commande. Veuillez réessayer.'
    error.value = errorMessage
  }
}
</script>

<style scoped></style>