import numpy as np

# Generar datos de ejemplo con los nuevos parámetros
np.random.seed(42)
n = 120
x = np.random.normal(0, 1, n)
true_beta0 = 0.5
true_beta1 = -1.2
true_sigma = 2.0  # σ = 2 ya que σ² = 4
y = true_beta0 + true_beta1 * x + np.random.normal(0, true_sigma, n)

# Estadísticas necesarias
x_bar = np.mean(x)
y_bar = np.mean(y)
sum_x_sq = np.sum(x**2)
sum_x = np.sum(x)
n_data = len(y)

def log_posterior(beta0, beta1, sigma, x, y):
    """Calcula el log-posterior no normalizado"""
    if sigma <= 0:
        return -np.inf
    
    # Log-verosimilitud
    y_pred = beta0 + beta1 * x
    ssr = np.sum((y - y_pred)**2)
    log_likelihood = -0.5 * n_data * np.log(2 * np.pi * sigma**2) - 0.5 * ssr / sigma**2
    
    # Log-priors
    log_prior_beta0 = -0.5 * (beta0**2) / 100
    log_prior_beta1 = -0.5 * (beta1**2) / 100
    log_prior_sigma = (2-1) * np.log(sigma) - sigma  # Gamma(2,1)
    
    return log_likelihood + log_prior_beta0 + log_prior_beta1 + log_prior_sigma

def mcmc_chain(n_iter=4000, burn_in=1000):
    """Ejecuta una cadena MCMC"""
    # Inicialización
    beta0 = np.random.normal(0, 1)
    beta1 = np.random.normal(0, 1)
    sigma = np.random.gamma(2, 1)
    
    samples = np.zeros((n_iter, 3))
    log_posteriors = np.zeros(n_iter)
    
    for i in range(n_iter):
        # 1. Muestrear β₀|β₁,σ,y
        prec_beta0 = n_data/sigma**2 + 1/100
        mean_beta0 = (n_data/sigma**2 * (y_bar - beta1 * x_bar)) / prec_beta0
        beta0 = np.random.normal(mean_beta0, 1/np.sqrt(prec_beta0))
        
        # 2. Muestrear β₁|β₀,σ,y
        sum_xy = np.sum(x * (y - beta0))
        prec_beta1 = sum_x_sq/sigma**2 + 1/100
        mean_beta1 = (sum_xy/sigma**2) / prec_beta1
        beta1 = np.random.normal(mean_beta1, 1/np.sqrt(prec_beta1))
        
        # 3. Muestrear σ|β₀,β₁,y usando Metropolis-Hastings
        ssr = np.sum((y - beta0 - beta1 * x)**2)
        
        # Distribución propuesta
        log_sigma_prop = np.log(sigma) + np.random.normal(0, 0.1)
        sigma_prop = np.exp(log_sigma_prop)
        
        # Ratio de aceptación
        current_log_posterior = (-(n_data-2)/2 * np.log(sigma) - ssr/(2*sigma**2) - sigma)
        proposed_log_posterior = (-(n_data-2)/2 * np.log(sigma_prop) - ssr/(2*sigma_prop**2) - sigma_prop)
        
        if np.log(np.random.uniform()) < (proposed_log_posterior - current_log_posterior):
            sigma = sigma_prop
        
        samples[i] = [beta0, beta1, sigma]
        log_posteriors[i] = log_posterior(beta0, beta1, sigma, x, y)
    
    return samples[burn_in:], log_posteriors[burn_in:]

# Ejecutar 4 cadenas MCMC
print("Ejecutando 4 cadenas MCMC...")
all_samples = []
all_log_posteriors = []

for chain in range(4):
    samples, log_posteriors = mcmc_chain()
    all_samples.append(samples)
    all_log_posteriors.append(log_posteriors)
    print(f"Cadena {chain+1} completada")

all_samples = np.vstack(all_samples)
all_log_posteriors = np.concatenate(all_log_posteriors)

print(f"Muestras generadas: {all_samples.shape}")

# Método 1: MAP como moda de las muestras MCMC
map_index = np.argmax(all_log_posteriors)
map_estimate = all_samples[map_index]

print("\nEstimación MAP (Método 1 - moda MCMC):")
print(f"β₀ = {map_estimate[0]:.4f}")
print(f"β₁ = {map_estimate[1]:.4f}")
print(f"σ = {map_estimate[2]:.4f}")

print(f"\nValores verdaderos:")
print(f"β₀ = {true_beta0:.4f}, β₁ = {true_beta1:.4f}, σ = {true_sigma:.4f}")

# Intervalos creíbles del 95%
def calculate_credible_intervals(samples):
    """Calcula intervalos creíbles del 95%"""
    lower = np.percentile(samples, 2.5, axis=0)
    upper = np.percentile(samples, 97.5, axis=0)
    return lower, upper

lower, upper = calculate_credible_intervals(all_samples)

print("\nIntervalos creíbles del 95%:")
print(f"β₀: [{lower[0]:.4f}, {upper[0]:.4f}]")
print(f"β₁: [{lower[1]:.4f}, {upper[1]:.4f}]")
print(f"σ: [{lower[2]:.4f}, {upper[2]:.4f}]")

# Estadísticas resumen
print("\nEstadísticas resumen:")
print(f"Media posterior β₀: {np.mean(all_samples[:, 0]):.4f} (verdadero: {true_beta0:.4f})")
print(f"Media posterior β₁: {np.mean(all_samples[:, 1]):.4f} (verdadero: {true_beta1:.4f})")
print(f"Media posterior σ: {np.mean(all_samples[:, 2]):.4f} (verdadero: {true_sigma:.4f})")
print(f"Desviación estándar posterior β₀: {np.std(all_samples[:, 0]):.4f}")
print(f"Desviación estándar posterior β₁: {np.std(all_samples[:, 1]):.4f}")
print(f"Desviación estándar posterior σ: {np.std(all_samples[:, 2]):.4f}")

# Verificar si los valores verdaderos están dentro de los intervalos creíbles
print("\nVerificación de intervalos creíbles:")
print(f"β₀ verdadero en IC: {lower[0] <= true_beta0 <= upper[0]}")
print(f"β₁ verdadero en IC: {lower[1] <= true_beta1 <= upper[1]}")
print(f"σ verdadero en IC: {lower[2] <= true_sigma <= upper[2]}")

