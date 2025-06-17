# 事前と事後の 'mu' の分布を比較
plt.figure(figsize=(8, 5))

# prior（線でプロット）
az.plot_kde(prior.prior["mu"].values.flatten(), label="Prior", linestyle="--")

# posterior（線でプロット）
az.plot_kde(trace.posterior["mu"].values.flatten(), label="Posterior", linestyle="-")

plt.legend()
plt.title("Prior vs Posterior Distribution for 'mu'")
plt.xlabel("mu")
plt.ylabel("Density")
plt.grid(True)
plt.show()


prior_samples = idata.prior["パラメータ名"].values.flatten()
plt.hist(prior_samples, bins=30, density=True, alpha=0.5, label="Prior")
plt.legend()
plt.show()
