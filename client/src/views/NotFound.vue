<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1 class="error-title">Page not found</h1>
      <p class="error-message">The page you are looking for does not exist or has been moved.</p>
      <router-link to="/" class="back-link">Back to Dashboard</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NotFound'
}
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 2rem;
}

.not-found-content {
  text-align: center;
  max-width: 400px;
}

.error-code {
  font-size: 6rem;
  font-weight: 700;
  color: #e2e8f0;
  line-height: 1;
  letter-spacing: -0.05em;
  margin-bottom: 1rem;
  /* Layered border effect to give the large number visual depth */
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 0.75rem;
}

.error-message {
  font-size: 0.938rem;
  color: #64748b;
  margin: 0 0 2rem;
  line-height: 1.5;
}

.back-link {
  display: inline-block;
  padding: 0.625rem 1.5rem;
  background: #0f172a;
  color: #ffffff;
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.back-link:hover {
  background: #1e293b;
}
</style>
