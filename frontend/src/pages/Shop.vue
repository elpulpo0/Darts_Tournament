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
        <input v-model="orderForm.address" placeholder="Adresse complète" required class="input-field" />
        <div class="form-buttons">
          <button type="submit">Confirmer la commande</button>
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

const products = ref<any[]>([])
const cart = ref<any[]>([])
const selectedVariants = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const showCheckout = ref(false)
const orderForm = ref({ name: '', email: '', address: '' })

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
  if (!orderForm.value.name || !orderForm.value.email || !orderForm.value.address) {
    return
  }
  const validCartItems = cart.value.filter(item => item.selectedVariant)
  if (validCartItems.length === 0) {
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
    const response = await backendApi.post('/api/printful/orders', orderData)
    if (response.data.result.id) {
      cart.value = []
      showCheckout.value = false
      orderForm.value = { name: '', email: '', address: '' }
    }
  } catch (err: any) {
    console.error('Erreur commande :', err)
  }
}
</script>

<style scoped>
.shop-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.shop-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.shop-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 0.5rem;
}

.shop-header p {
  font-size: 1.1rem;
  color: var(--color-text);
  max-width: 600px;
  margin: 0 auto;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.product-card {
  background: wheat;
  border-radius: var(--radius);
  padding: 1.5rem;
  box-shadow: 0 2px 8px var(--color-shadow);
  transition: transform 0.3s ease;
}

.product-image {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: var(--radius);
  margin-bottom: 1rem;
}

.product-card h3 {
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--color-primary);
  margin: 0.5rem 0;
}

.price {
  font-size: 1.2rem;
  color: var(--color-secondary);
  margin: 0.5rem 0;
}

.variants-selector {
  margin: 1rem 0;
}

.color-selector,
.size-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.variant-label {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text);
}

.variants {
  list-style: none;
  padding: 0;
  display: flex;
  gap: 0.5rem;
}

.variant-color {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.variant-color:hover,
.variant-color.selected {
  border-color: var(--color-accent);
  transform: scale(1.15);
}

.size-selector select {
  padding: 0.5rem;
  border: 1px solid var(--color-shadow);
  border-radius: var(--radius);
  font-size: 1rem;
  cursor: pointer;
}

.no-variants,
.no-products {
  font-style: italic;
  color: var(--color-accent);
  margin: 1rem 0;
}

.cart-summary {
  margin: 2rem auto;
  padding: 1.5rem;
  background: wheat;
  border-radius: var(--radius);
  box-shadow: 0 2px 8px var(--color-shadow);
  max-width: 500px;
}

.remove-button {
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.3s ease;
}

.checkout-form {
  margin: 2rem auto;
  padding: 1.5rem;
  background: wheat;
  border-radius: var(--radius);
  box-shadow: 0 2px 8px var(--color-shadow);
  max-width: 500px;
}

.checkout-form h3 {
  font-size: 1.4rem;
  color: var(--color-primary);
  margin-bottom: 1rem;
}

.input-field {
  width: 100%;
  padding: 0.8rem;
  margin: 0.5rem 0;
  border: 1px solid var(--color-shadow);
  border-radius: var(--radius);
  font-size: 1rem;
}

.form-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.back-link {
  display: inline-block;
  margin-top: 2rem;
  padding: 0.5rem 1rem;
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.back-link:hover {
  color: var(--color-primary);
}

.loading,
.error {
  padding: 2rem;
  font-size: 1.2rem;
  color: var(--color-accent);
  text-align: center;
}

.cart-item-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .shop-page {
    padding: 1rem;
  }

  .shop-header h1 {
    font-size: 2rem;
  }

  .products-grid {
    grid-template-columns: 1fr;
  }

  .product-image {
    max-height: 200px;
  }

  .variant-color {
    width: 24px;
    height: 24px;
  }

  .cart-summary {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>