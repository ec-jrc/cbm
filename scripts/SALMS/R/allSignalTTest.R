

#'  Calculate t-test-statistics for differences between week0 and surrounding weeks
#'  of signal functions for all activity types and signals
#' 
#' 
#' @eval salmsparam("allvar")
#' @eval salmsparam("stats")
#' @eval salmsparam("events")
#' @eval salmsparam("first")
#' @eval salmsparam("dels")
#' @eval salmsparam("weighted")
#' @eval salmsparam("EVcol")
#' @eval salmsparam("inds")
#' @eval salmsparam("weeks")
#' @eval salmsparam("week0u")
#' @eval salmsparam("weekcorrect")
#' @eval salmsparam("plotit")
#' @eval salmsparam("sepPlots")
#' @eval salmsparam("devsAllTTests")
#' @eval salmsparam("yranges")
#' @eval salmsparam("legend")
#' 
#' 
#' 
#' @references{
#'   \insertRef{Zielinski2022}{SALMS}
#' }
#' 
#' @examples 
#' ddir = system.file("extdata", package = "SALMS")
#' odir = paste0(ddir, "/signals")
#' 
#' hdir = tempdir()
#' # Read all signals and find the names of all signals and indicators
#' allvar = readSignals(odir)
#' inds = names(allvar)
#' # Create three pdfs for t-test output
#' devs = list()
#' for (ipdf in 1:3) {pdf(paste0(hdir, "/ttest", ipdf, ".pdf")) ; devs[ipdf] = dev.cur()}
#' 
#' dfs = allSignalTTests(allvar, first = FALSE, dels = 0, weighted = FALSE,
#'                      inds = inds, dev = devs, weeks = 1:15, 
#'                      week0 = 7, weekcorrect = 0, plotit = TRUE, 
#'                      legend = "before") 
#' # Close the pdfs
#' for (ipdf in 1:3) dev.off(devs[ipdf])
#' 
#' @export
allSignalTTests = function(allvar, stats, events, first = FALSE, dels = 0, weighted = FALSE,
                          EVcol, sepPlots = NULL,
                          inds, weeks = 1:15, week0 = 7, weekcorrect = 0, plotit = FALSE, 
                          devs, yranges = NULL, legend = TRUE) {
  
  
  if (missing(EVcol)) EVcol = getEVcol(names(allvar[[1]]))
  if (missing(events)) events = unique(allvar[[1]][, EVcol])
  if (missing(inds)) inds = names(allvar)
  if (missing(stats)) stats = bnms
  
  cases = matrix(NA, ncol = length(inds), nrow = length(events))
  
  pbl = length(allvar) * length(events)
  if (interactive() ) pb = txtProgressBar(1, pbl, style = 3)

  dfs = list()
  sepBands = sepStats = NULL
  if (!is.null(sepPlots)) {
    if ("bands" %in% names(sepPlots)) sepBands = sepPlots$bands else sepBands = sepPlots
    if ("stats" %in% names(sepPlots)) sepStats = sepPlots$stats else sepStats = "P50"
  }
  if (!isFALSE(plotit) && is(devs, "character")) {
    fdevs = devs
    if (length(devs) == 1) {
      devs1 = paste0(devs, ".pdf")
      devs2 = NULL
        if (length(sepBands) > 0) {
        devs2 = paste0(paste(devs, c("all", names(sepBands))), ".pdf")
        }
      devs = c(devs1, devs2)
    }
    devs = list()
    for (idev in 1:length(fdevs)) {pdf(fdevs[idev]); devs[[idev]] = dev.cur()}
    on.exit(for (idev in 1:length(devs)) dev.off(devs[[idev]]))
  } else fdevs = NULL
  if (is.null(yranges)) yranges = list()
  for (ia in 1:length(events)) {
    atyp = events[[ia]]
    dfs[[ia]] = list()
    #  retdats[[ia]] = list()
    # Loop over the different indices
    for (iind in 1:length(allvar)) {
      ind = inds[iind]
      allv = allvar[[iind]]
      allv = allv[allv[, EVcol] %in% atyp,]
      if (is.null(allv) || dim(allv)[1] == 0) next
      cases[ia, iind] = max(table(allv$WEEK))
      yrange = yranges[[ind]] 
      
      # compute t.test for the weekly values for a signal/acitivity type
      dfl = signalTTest(allv, stats = stats, events = events, first = first,
                        dels = dels, weighted = weighted, sepPlots = sepPlots,
                        weeks = weeks, week0 = week0, weekcorrect = weekcorrect, plotit = plotit, 
                        
                        
                        devs = devs,
                        main = c(paste(atyp, collapse = " "), paste(cases[ia,iind])),
                        ind = inds[iind], yrange = yrange, legend = legend)  
      # Store the results in dfs
      dfs[[ia]][[iind]] = dfl$df
      if (is.null(yranges[[ind]])) yranges[[ind]] = dfl$yrange
      
      # This would be for additional analyses, can be removed
      #retdats[[ia]][[iind]] = allv[allv$WEEK %in%  7:13, ]
      
      
#      print(paste("iind done", week0, ia,"/",length(events), 
#                  iind, cases[ia, iind]))
      if (interactive()) setTxtProgressBar(pb, (ia-1)*length(allvar) + iind)
      
    }
  }
  dfs
}
