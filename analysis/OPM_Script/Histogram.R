library(ggplot2)
library(viridis)
library(scales)
library(ggtech)  # Load ggtech

# Function to find the minimum non-zero value in a given column of a data frame
find_min_non_zero <- function(data, column_name) {
  min_value <- min(data[[column_name]][data[[column_name]] > 0])
  return(min_value)
}

# Assuming 'data_melted' is a data frame and 'value' is the column with your data
# Calculate the width of the bins
binwidth <- (max(data_melted$value) - min(data_melted$value)) / 20 # Adjust 20 to the number of bins you want

# Define your ggplot object
p <- ggplot(data_melted, aes(x = value)) +
  annotation_custom(gradient_raster, xmin = 550, xmax = 15550, ymin = -Inf, ymax = Inf) +
  geom_line(stat = "density", aes(y = ..count..), color = "cyan", size = .5, adjust = 1/binwidth) +
  labs(title = "Color Key and Histogram", x = "Value", y = "Count") +
  theme_tech(theme = "etsy") +  # Apply Etsy theme from ggtech
  theme(
    plot.background = element_rect(fill = "transparent", color = NA),
    plot.title = element_text(hjust = 0.5),
    plot.margin = margin(5, 5, 5, 5),
    legend.position = "top"
  )

# Define the smallest non-zero value and the upper limit for the breaks
smallest_value <- min(data_melted$value[data_melted$value > 0])
upper_limit <- max(data_melted$value)

# Create a sequence from 0 to the upper limit by 5000
breaks_5k <- seq(0, upper_limit, by = 5000)

# If the smallest value is close to zero, exclude the zero from the sequence
if(smallest_value < 2500) {
  breaks_5k <- breaks_5k[-1]
}

# Combine the smallest value with the regular 5k increments, ensuring no duplicates
breaks_combined <- unique(c(smallest_value, breaks_5k))

# Update the plot object with the new breaks and ensure the title is black
p <- p + scale_x_continuous(breaks = breaks_combined, labels = scales::number_format(scale = 1e-3, suffix = "k")) +
  theme(plot.title = element_text(hjust = 0.5, color = "black"))  # Set title color to black

# Print the plot
print(p)
