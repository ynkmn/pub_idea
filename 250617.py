prior_samples = idata.prior["パラメータ名"].values.flatten()
plt.hist(prior_samples, bins=30, density=True, alpha=0.5, label="Prior")
plt.legend()
plt.show()
