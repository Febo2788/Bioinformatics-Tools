
library(ggplot2)
library(viridis)
library(opm)
library(reshape2)
knitr::opts_chunk$set(echo = TRUE, cache = TRUE)
# Specify the directory containing the CSV files
dir_path <- "C:/Users/thora/Downloads/TT12AB/converted_files"

# Automatically detect all CSV files in the directory
file_paths <- list.files(path = dir_path, pattern = "\\.csv$", full.names = TRUE)
file_names <- basename(file_paths)

# Extract and format the desired portion of the file name for use as row labels
row_labels <- sapply(file_names, function(name) {
  parts <- unlist(strsplit(name, "_"))
  paste(parts[1], parts[5], sep = "-")
})

# Extract MBT numbers for ordering
mbt_numbers <- sapply(row_labels, function(label) {
  as.numeric(sub(".*-", "", label))
})

# Order file paths and row labels by MBT numbers
ordered_indices <- order(mbt_numbers)
file_paths <- file_paths[ordered_indices]
row_labels <- row_labels[ordered_indices]

# Read and process each file to extract the AUC data
results <- lapply(file_paths, function(file) {
  result <- read_single_opm(file)
  aggregated_result <- do_aggr(result, method = "opm-fast", boot = 0)
  # Flatten the matrix to a single row
  auc_data <- c(aggregated_result@aggregated["AUC", ])
  return(auc_data)
})

# Combine the AUC data from all files into one matrix
combined_auc_data <- do.call(rbind, results)
rownames(combined_auc_data) <- row_labels

# Melt the data for ggplot2
data_melted <- melt(combined_auc_data)

# Adjusting the positions where horizontal lines should be drawn
hline_positions <- seq(3, nrow(combined_auc_data)-1, by = 2.0)-.5

# Reverse the y-axis order
data_melted$Var1 <- factor(data_melted$Var1, levels = rev(unique(data_melted$Var1)))
# Base plot
max_x_pos <- length(unique(data_melted$Var2))

# Creating a dataframe for segments
segments_df <- data.frame(
  x = rep(0.5, length(hline_positions)),
  xend = rep(max_x_pos + 0.5, length(hline_positions)), # Added 0.5 to extend by half a square
  y = hline_positions,
  yend = hline_positions
)

p <- ggplot(data = data_melted, aes(Var2, Var1)) +
  geom_tile(aes(fill = value), color = "white", size = 0.1) + 
  scale_fill_viridis(direction = 1) +
  geom_segment(data = segments_df, aes(x = x, xend = xend, y = y, yend = yend), color ="black", size = .5) +
  labs(fill = "value", title = "AUC Heatmap") +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1),
    axis.text.y = element_text(size = 8),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    legend.position = "right"
  )

print(p)
