return {
	"nvim-treesitter/nvim-treesitter",
	opts = function(_, opts)
		vim.filetype.add({
			pattern = {
				[".*ya?ml"] = "yaml.ansible",
			},
		})

		vim.filetype.add({
			extension = { j2 = "yaml.ansible" },
		})
	end,
}
