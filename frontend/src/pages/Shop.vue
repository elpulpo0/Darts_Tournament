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
      <div v-for="(product, index) in products" :key="product.id" class="product-card">
        <img :src="getMainImage(product, selectedVariants[index])" :alt="product.name" loading="lazy" />
        <h3>{{ product.name }}</h3>
        <p v-if="hasVariants(product)">Prix : {{ getCurrentPrice(product, selectedVariants[index]) }}€</p>
        <div v-if="hasVariants(product)" class="variants-selector">
          <ul class="variants">
            <li
              v-for="variant in product.sync_variants"
              :key="`v-${variant.id}`"
              @click="selectVariant(index, variant)"
              :class="{ selected: selectedVariants[index]?.id === variant.id }"
              class="variant-color"
              :style="{ backgroundColor: getColorForVariant(variant.name) }"
              :title="variant.name"
            >
              <!-- Petit carré vide, couleur en background -->
            </li>
          </ul>
        </div>
        <p v-else class="no-variants">Variantes non configurées (contacte-nous !)</p>
        <button @click="addToCart(product, selectedVariants[index])" class="btn-buy" :disabled="!hasVariants(product) || !selectedVariants[index]">
          Ajouter au panier
        </button>
      </div>
    </div>
    <!-- Panier simple -->
    <div v-if="cart.length" class="cart-summary">
      <h3>Panier ({{ cart.length }} produit{{ cart.length > 1 ? 's' : '' }})</h3>
      <button @click="openCheckoutForm" class="btn-checkout">Valider</button>
    </div>
    <!-- Formulaire checkout -->
    <div v-if="showCheckout" class="checkout-form">
      <h3>Infos livraison</h3>
      <form @submit.prevent="submitOrder">
        <input v-model="orderForm.name" placeholder="Nom complet" required />
        <input v-model="orderForm.email" type="email" placeholder="Email" required />
        <input v-model="orderForm.address" placeholder="Adresse complète (Hérault prioritaire)" required />
        <button type="submit" class="btn-buy">Confirmer commande</button>
      </form>
      <button @click="showCheckout = false">Annuler</button>
    </div>
    <router-link to="/home" class="back-link">← Retour à l'accueil</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const products = ref<any[]>([])
const cart = ref<any[]>([])
const selectedVariants = ref<any[]>([])  // Un par produit
const loading = ref(true)
const error = ref('')
const showCheckout = ref(false)
const orderForm = ref({ name: '', email: '', address: '' })

// Token depuis .env
const PRINTFUL = import.meta.env.VITE_PRINTFUL

// Placeholder image base64
const placeholderImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk1lcmNoIEJhZGFydHM8L3RleHQ+PC9zdmc+'

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
  if (!PRINTFUL) {
    error.value = 'Token Printful manquant dans .env'
    loading.value = false
    return
  }
  try {
    const summaryResponse = await axios.get('/api/printful/store/products', {
      headers: { 
        Authorization: `Bearer ${PRINTFUL}`,
        'X-PF-Store-Id': 'badarts'
      }
    })
    const summaries = summaryResponse.data.result.slice(0, 3)

    if (summaries.length === 0) {
      error.value = 'Aucun produit trouvé sur Printful'
      loading.value = false
      return
    }

    const fullProducts = await Promise.all(
      summaries.map(async (summary: any) => {
        const detailResponse = await axios.get(`/api/printful/store/products/${summary.id}`, {
          headers: { 
            Authorization: `Bearer ${PRINTFUL}`,
            'X-PF-Store-Id': 'badarts'
          }
        })
        return detailResponse.data.result
      })
    )

    products.value = fullProducts
    selectedVariants.value = fullProducts.map(() => null)
    loading.value = false
  } catch (err: any) {
    console.error('Erreur détaillée :', err)
    error.value = 'Erreur API Printful : ' + (err.response?.data?.message || 'Vérifie token/scopes ou proxy')
    loading.value = false
  }
})

const hasVariants = (product: any) => {
  return product.sync_variants && Array.isArray(product.sync_variants) && product.sync_variants.length > 0
}

const selectVariant = (productIndex: number, variant: any) => {
  selectedVariants.value[productIndex] = variant
}

const getColorForVariant = (name: string) => {
  const colorPart = name.split('/')[1]?.trim() || name.trim()
  const normalizedColor = colorPart === 'Grey' ? 'Gray' : colorPart
  const color = colorMap[normalizedColor] || '#CCCCCC'
  return color
}

const getMainImage = (product: any, selectedVariant: any = null) => {
  if (selectedVariant?.files?.[0]?.url) {
    return selectedVariant.files[0].url
  }
  if (product.sync_product?.thumbnail_url) {
    return product.sync_product.thumbnail_url
  }
  // Fallback
  return placeholderImage
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
    alert('Sélectionne une variante !')
    return
  }
  cart.value.push({ ...product, selectedVariant, quantity: 1 })
  alert('Ajouté au panier !')
}

const openCheckoutForm = () => {
  showCheckout.value = true
}

const submitOrder = async () => {
  if (!orderForm.value.name || !orderForm.value.email || !orderForm.value.address) {
    alert('Remplis tous les champs')
    return
  }
  const validCartItems = cart.value.filter(item => item.selectedVariant)
  if (validCartItems.length === 0) {
    alert('Panier vide ou sans variantes sélectionnées')
    return
  }
  try {
    const orderData = {
      recipient: {
        name: orderForm.value.name,
        email: orderForm.value.email,
        address1: orderForm.value.address,
        country_code: 'FR',
      },
      items: validCartItems.flatMap((item: any) => [
        { sync_variant_id: item.selectedVariant.id, quantity: item.quantity }
      ])
    }
    const response = await axios.post('/api/printful/orders', orderData, {
      headers: { 
        Authorization: `Bearer ${PRINTFUL}`,
        'Content-Type': 'application/json',
        'X-PF-Store-Id': 'badarts'
      }
    })
    if (response.data.result.id) {
      alert(`Commande créée ! ID: ${response.data.result.id}. Tu recevras un email de Printful.`)
      cart.value = []
      showCheckout.value = false
      orderForm.value = { name: '', email: '', address: '' }
    }
  } catch (err: any) {
    console.error('Erreur commande :', err)
    alert('Erreur commande : ' + (err.response?.data?.error?.message || 'Réessaie'))
  }
}
</script>

<style scoped>
.shop-page { max-width: 1200px; margin: 0 auto; padding: 2rem; text-align: center; }
.shop-header { margin-bottom: 2rem; }
.shop-header h1 { font-size: 2.5rem; color: var(--color-mascot); }
.products-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
.product-card { border: 1px solid var(--color-light-shadow); padding: 1rem; border-radius: var(--radius); }
.product-card img { max-width: 100%; height: 200px; object-fit: cover; border-radius: var(--radius); }
.variants-selector { margin: 1rem 0; text-align: left; }
.variants-selector label { display: block; font-weight: bold; margin-bottom: 0.5rem; }
.variants { list-style: none; padding: 0; display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: center; }
.variant-color { 
  width: 30px; 
  height: 30px; 
  border-radius: 50%;  /* Carré arrondi pour cap */
  cursor: pointer; 
  transition: all 0.3s; 
  border: 2px solid transparent;
  position: relative;
}
.variant-color:hover, .variant-color.selected { 
  transform: scale(1.1); 
  border-color: var(--color-accent); 
}
.variant-color::after {  /* Tooltip nom couleur */
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-bg);
  color: var(--color-fg);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius);
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s;
  z-index: 10;
}
.variant-color:hover::after {
  opacity: 1;
  visibility: visible;
}
.no-variants, .no-products { font-style: italic; color: var(--color-accent); margin: 1rem 0; }
.btn-buy:disabled { background: var(--color-light-shadow); cursor: not-allowed; }
.btn-buy, .btn-checkout { background: var(--color-mascot); color: white; padding: 0.75rem 1.5rem; border: none; border-radius: var(--radius); cursor: pointer; margin: 0.5rem; }
.btn-buy:hover:not(:disabled), .btn-checkout:hover { background: var(--color-success); }
.cart-summary { margin-top: 2rem; padding: 1rem; background: var(--color-bg-secondary); border-radius: var(--radius); }
.checkout-form { margin-top: 1rem; padding: 1rem; background: var(--color-light-shadow); border-radius: var(--radius); text-align: left; max-width: 400px; margin: 1rem auto; }
.checkout-form input { display: block; width: 100%; margin: 0.5rem 0; padding: 0.5rem; border: 1px solid var(--color-accent); border-radius: var(--radius); }
.back-link { display: inline-block; margin-top: 2rem; padding: 0.5rem 1rem; background: var(--color-accent); color: var(--color-bg); text-decoration: none; border-radius: var(--radius); }
.loading, .error { padding: 2rem; font-size: 1.2rem; color: var(--color-accent); }
@media (max-width: 768px) { 
  .products-grid { grid-template-columns: 1fr; } 
  .shop-header h1 { font-size: 2rem; } 
  .checkout-form { max-width: 100%; }
  .variants { gap: 0.25rem; }
  .variant-color { width: 25px; height: 25px; }
}
</style>