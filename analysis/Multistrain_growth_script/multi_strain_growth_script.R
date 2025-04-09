# Required libraries
install.packages(c("ggplot2", "dplyr", "tidyr", "purrr"))
library(ggplot2)
library(dplyr)
library(tidyr)
library(purrr)

# Paths to the files
file_paths <- c(
  "C:/Users/thora/Downloads/TT12AB/converted_files/TT12B_SAM129320_STEC-O157_MBT_9_33_MBT_462_2#14#2023_A_20A_30.csv",
  "C:/Users/thora/Downloads/TT12AB/converted_files/TT12A_SAM129319_STECO157_MBT_9_33_MBT_462_2#9#2023_A_20A_10.csv",
  "C:/Users/thora/Downloads/TT12AB/converted_files/TT12B_SAM129320_STEC-O157_MBT_10_33_MBT_462_2#14#2023_A_20B_31.csv",
  "C:/Users/thora/Downloads/TT12AB/converted_files/TT12A_SAM129319_STECO157_MBT_10_33_MBT_462_2#9#2023_A_20B_11.csv"
)

# Title naming function
get_title <- function(name) {
  parts <- unlist(strsplit(name, "_"))
  paste(parts[1], paste("PM", parts[5], sep="-"), sep="-")
}

# Process each file and combine into a single dataframe
all_data <- map_dfr(file_paths, function(file_path) {
  # Read the data
  df <- read.csv(file_path)
  
  # Compute the average of wells from A01 to H12
  df$Average <- rowMeans(df[, c("A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10", "A11", "A12",
                                "B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B10", "B11", "B12",
                                "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12",
                                "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10", "D11", "D12",
                                "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12",
                                "F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "F12",
                                "G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G10", "G11", "G12",
                                "H01", "H02", "H03", "H04", "H05", "H06", "H07", "H08", "H09", "H10", "H11", "H12")])
  
  # Add a 'Source' column for the title (to distinguish in the plot)
  df$Source <- get_title(basename(file_path))
  
  return(df)
})

# Plot the combined data
plot <- ggplot(all_data, aes(x = Hour, y = Average, color = Source, linetype = Source)) +
  geom_line() +
  ggtitle("Strain Growth over Time") +
  xlab("Hour") +
  ylab("Average Well Value") +
  theme_minimal() +
  scale_color_brewer(palette = "Set1") +
  theme(legend.title = element_blank())

print(plot)
