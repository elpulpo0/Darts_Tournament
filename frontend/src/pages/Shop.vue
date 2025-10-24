<template>
  <div class="shop-page">
    <header class="shop-header">
      <h1>Boutique Badarts</h1>
      <p>Nos t-shirts, maillots et casquettes personnalisés. Fabriqués sur demande – commande et soutiens le club !</p>
    </header>
    <div v-if="loading" class="loading">Chargement des produits...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="products-grid">
      <div v-for="product in products" :key="product.id" class="product-card">
        <img :src="getMainImage(product)" :alt="product.name" loading="lazy" />
        <h3>{{ product.name }}</h3>
        <p v-if="product.variants.length">À partir de {{ getMinPrice(product) }}€</p>
        <ul class="variants">
          <li v-for="variant in product.variants.slice(0, 3)" :key="variant.id">
            {{ variant.name }} - {{ variant.price }}€
          </li>
        </ul>
        <button @click="addToCart(product)" class="btn-buy">Ajouter au panier</button>
      </div>
    </div>
    <!-- Panier simple -->
    <div v-if="cart.length" class="cart-summary">
      <h3>Panier ({{ cart.length }} item{{ cart.length > 1 ? 's' : '' }})</h3>
      <button @click="openCheckoutForm" class="btn-checkout">Passer à la caisse</button>
    </div>
    <!-- Formulaire checkout (simple, étends avec ton auth si besoin) -->
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
const loading = ref(true)
const error = ref('')
const showCheckout = ref(false)
const orderForm = ref({ name: '', email: '', address: '' })

// Token depuis .env
const PRINTFUL = import.meta.env.VITE_PRINTFUL

onMounted(async () => {
  if (!PRINTFUL) {
    error.value = 'Token Printful manquant dans .env'
    loading.value = false
    return
  }
  try {
    const response = await axios.get('https://api.printful.com/store/products', {
      headers: { Authorization: `Bearer ${PRINTFUL}` }
    })
    products.value = response.data.result.slice(0, 3)  // Limite à tes 3 produits
    loading.value = false
  } catch (err: any) {
    error.value = 'Erreur API Printful : ' + (err.response?.data?.message || 'Vérifie token/scopes')
    loading.value = false
  }
})

const getMainImage = (product: any) => {
  const variant = product.variants[0]
  return variant?.files?.[0]?.url || '/assets/placeholder-merch.png'  // Ajoute un placeholder si besoin
}

const getMinPrice = (product: any) => {
  return Math.min(...product.variants.map((v: any) => parseFloat(v.price))).toFixed(2)
}

const addToCart = (product: any) => {
  cart.value.push({ ...product, quantity: 1 })
  alert('Ajouté au panier !')  // Remplace par toast si tu as une lib
}

const openCheckoutForm = () => {
  showCheckout.value = true
}

const submitOrder = async () => {
  if (!orderForm.value.name || !orderForm.value.email || !orderForm.value.address) {
    alert('Remplis tous les champs')
    return
  }
  try {
    const orderData = {
      recipient: {
        name: orderForm.value.name,
        email: orderForm.value.email,
        address1: orderForm.value.address.split(',')[0],
        // Ajoute plus si besoin : city, country_code: 'FR', etc.
      },
      items: cart.value.flatMap((item: any) =>
        item.variants.map((v: any) => ({ sync_variant_id: v.id, quantity: item.quantity }))
      )
    }
    const response = await axios.post('https://api.printful.com/orders', orderData, {
      headers: { Authorization: `Bearer ${PRINTFUL}` }
    })
    if (response.data.result.id) {
      alert(`Commande créée ! ID: ${response.data.result.id}. Tu recevras un email de Printful.`)
      cart.value = []
      showCheckout.value = false
      orderForm.value = { name: '', email: '', address: '' }
      // Option : Redirige vers merci ou dashboard
    }
  } catch (err: any) {
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
.variants { list-style: none; padding: 0; font-size: 0.9rem; text-align: left; }
.btn-buy, .btn-checkout { background: var(--color-mascot); color: white; padding: 0.75rem 1.5rem; border: none; border-radius: var(--radius); cursor: pointer; margin: 0.5rem; }
.btn-buy:hover, .btn-checkout:hover { background: var(--color-success); }
.cart-summary { margin-top: 2rem; padding: 1rem; background: var(--color-bg-secondary); border-radius: var(--radius); }
.checkout-form { margin-top: 1rem; padding: 1rem; background: var(--color-light-shadow); border-radius: var(--radius); text-align: left; max-width: 400px; margin: 1rem auto; }
.checkout-form input { display: block; width: 100%; margin: 0.5rem 0; padding: 0.5rem; border: 1px solid var(--color-accent); border-radius: var(--radius); }
.back-link { display: inline-block; margin-top: 2rem; padding: 0.5rem 1rem; background: var(--color-accent); color: var(--color-bg); text-decoration: none; border-radius: var(--radius); }
.loading, .error { padding: 2rem; font-size: 1.2rem; color: var(--color-accent); }
@media (max-width: 768px) { 
  .products-grid { grid-template-columns: 1fr; } 
  .shop-header h1 { font-size: 2rem; } 
  .checkout-form { max-width: 100%; }
}
</style>