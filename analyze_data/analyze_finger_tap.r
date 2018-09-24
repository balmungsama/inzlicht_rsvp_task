import_tap <- function(filename) {

  filename <- "/mnt/c/Users/enter/OneDrive - University of Toronto/Labs/Inzlicht Lab/outside_project/experiment/finger_tapping/data/123_finger_tap_2018_Sep_24_1431.csv"
  
  data <- read.csv(filename, stringsAsFactors = F)
  
  behav_rts <- data$button_press.rt
  behav_rts <- behav_rts[ !vapply(behav_rts, function(x) {x==""}, logical(1)) ]
  behav_rts <- gsub("\\[|\\]", "", behav_rts)
  behav_rts <- unlist(strsplit(behav_rts, ','))
  behav_rts <- as.numeric(behav_rts)

  return(behav_rts)
}

conv_relative_rts <- function(behav_rts) {
  behav_rts_relative <- behav_rts

  for (rt in length(behav_rts_relative):1) {
    if (rt != 1) {
      behav_rts_relative[rt] <- behav_rts_relative[rt] - behav_rts_relative[rt - 1]
    }
  }

  behav_rts_relative <- behav_rts_relative[-1]

  return(behav_rts_relative)
}

fourier_relative_rts <- function(behav_rts_relative) {
  if(!require("install.load")) {install.packages("install.load")}
  install.load::install_load("stats")
  install.load::install_load("TSA")

  p <- periodogram(behav_rts)
}

m_sd_rt <- function(behav_rts_relative) {
  rt_summary <- data.frame(mean = mean(behav_rts_relative), sd = sd(behav_rts_relative))
  return(rt_summary)
}

rt_plot <- function(behav_rts_relative, output_path, subjid) {
  n_resp = 1:length(behav_rts_relative)
  
  output_path <- file.path(output_path, paste0(subjid, "_RTplot", ".jpg"))

  jpeg(output_path)
  plot(x = n_resp, y = behav_rts_relative, ylim = c(0,1), xlab = "trials", ylab = "response time (s)", main = subjid)
  abline(lm(behav_rts_relative ~ n_resp), col = "red")
  dev.off()

}

exgauss_rt <- function(behav_rts_relative, output_path, subjid) {
  if(!require("install.load")) {install.packages("install.load")}
  install.load::install_load("retimes")

  output_path <- file.path(output_path, paste0(subjid, "_exGplot", ".jpg"))

  jpeg(output_path)
  rt_exg <- timefit(behav_rts_relative, plot=T)
  abline(v=.6, col = "red")
  dev.off()
}