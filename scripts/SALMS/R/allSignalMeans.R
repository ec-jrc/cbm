
#' Create means of signal functions for all activity types and signals
#' 
#' The function computes mean and standard deviation for a particular 
#' activity type, for the descriptors included in the stats variable.
#' 
#'  
#' @eval salmsparam("allvar")
#' @eval salmsparam("stats")
#' @eval salmsparam("events")
#' @eval salmsparam("first") 
#' @eval salmsparam("dels") 
#' @eval salmsparam("yranges")
#' @eval salmsparam("weighted")
#' @eval salmsparam("inds")
#' @eval salmsparam("weeks")
#' @eval salmsparam("week0u")
#' @eval salmsparam("weekcorrect")
#' @param plotit Should the function plot anything? Either FALSE, "boxplot", "graph"
#'   or "both"
#' @param plotCumsum Should the function also plot means and uncertainty for
#'           the cumulative sums?
#' @eval salmsparam("devsAllMeans")
#' @eval salmsparam("sepPlots")
#' @param zeroshift Logical; should all activity centred time series be shifted according to the value at week0?
#' @eval salmsparam("FOIinfo")
#' @eval salmsparam("legend")
#' @eval salmsparam("addNum")
#' @eval salmsparam("iprint")
#' @eval salmsparam("drop")
#' 
#' @details
#' The function produces plots for all signals and descriptors for different activity
#' types. It will also return an array (typically referred to as \code{evres}) that can be used 
#' by further functions in this package.
#' 
#' #' @details `r salmsdetails("evresvar")`

#' 
#' @returns 
#' A list with two elements, an array with the different results, and a vector with the number
#' of cases for each combination of activity type and signal. The array (named evres) is 
#' created as a five dimensional array with the following structure:
#' 
#' `evres = array(NA, dim = c(length(events), length(inds), ` 
#' `            length(stats), 20, length(weeks)))`
#' 
#' The length of the fourth dimensions is 20, although there are only values in the first 4 items after 
#' \code{allSignalMeans}.
#' The rest will be computed and used in the function \code{\link{signalProbability}}. 
#' If \code{isTRUE(drop)} and there is only one activity type, the first dimension will be dropped.
#' The values in these first four items are 
#' \itemize{
#'   \item{1: The difference in signal value between \code{week0} and the week in question}
#'   \item{2: The cumulative difference in signal value between \code{week0} and the week in question}
#'   \item{3: The standard deviation of the difference in signal value between \code{week0} and the week in question}
#'   \item{4: The standard deviation of the cumulative difference in signal value between \code{week0} and the week in question}
#' }
#' 
#' The second element of the return value (referred to as cases) is a matrix with dimensions:
#' 
#' `cases = matrix(NA,  nrow = length(events), ncol = length(inds))` 
#' 
#' This is used for adding the number of cases to the header of some of the plots
#'
#'
#' @references{
#'   \insertRef{Zielinski2022}{SALMS}
#' }
#'
#' 
#' @examples 
#' ddir = system.file("extdata", package = "SALMS")
#' odir = paste0(ddir, "/signals")
#' 
#' hdir = tempdir()
#' # Read all signals and find the names of all signals/indicators
#' allvar = readSignals(odir)
#' inds = names(allvar)
#' 
#' # Open two pdfs for plotting the results from the mean function 
#' devs = list()
#' for (ipdf in 1:2) {pdf(paste0(hdir, "/meanPlot", ipdf, ".pdf")) ; devs[ipdf] = dev.cur()}
#' 
#' # Store all the results from the calculations in evress, which contains an 
#' # array with the means and standard deviations
#' evress = allSignalMeans(allvar, events = 1, first = FALSE, 
#'                         dels = 0, weighted = FALSE, inds = inds, weeks = 1:15, week0 = 7, 
#'                         weekcorrect = 0, plotit = "both", 
#'                         dev = devs, zeroshift = TRUE, legend = "before",
#'                         addNum = FALSE, iprint = 1)
#' evres = evress$evres
#' cases = evress$cases
#' for (ipdf in 1:2) dev.off(devs[ipdf])
#' 
#' @export
allSignalMeans = function(allvar, stats, events, first = FALSE, dels = 0, yranges, weighted = FALSE,
                          inds, weeks = 1:15, week0 = 7, weekcorrect = 0, plotit = FALSE, 
                          plotCumsum = FALSE, devs, sepPlots = NULL, zeroshift = TRUE, FOIinfo, legend = TRUE,
                          addNum = FALSE, iprint = 1, drop = TRUE) {

  
  EVcol = getEVcol(names(allvar[[1]]))
  if (length(EVcol) == 0) {for (ii in 1:length(allvar)) allvar[[ii]]$EVENT_TYPE = 1}; EVcol = which(names(allvar[[1]]) == "EVENT_TYPE")
  if (missing(events)) events = unique(allvar[[1]][, EVcol])
  if (missing(inds)) inds = names(allvar)
  if (missing(stats)) stats = bnms

  
  pbl = length(allvar) * length(events)
  #' @importFrom utils txtProgressBar
  if (interactive() & iprint == 1) pb = txtProgressBar(1, pbl, style = 3)
  
  sepBands = sepStats = NULL
  if (!is.null(sepPlots)) {
    if ("bands" %in% names(sepPlots)) sepBands = sepPlots$bands else sepBands = sepPlots
    if ("stats" %in% names(sepPlots)) sepStats = sepPlots$stats else sepStats = "P50"
  }
  if (!missing(devs) && is(devs, "character")) {
    if (length(devs) == 1) {
      devs1 = paste0(devs, "_all.pdf")
      if (length(sepBands) > 0) devs1 = c(devs1, paste0(paste(devs, names(sepBands), sep = "_"), ".pdf"))
      if (isTRUE(plotit) | plotit == "both") {
          devs2 = gsub(".pdf", "_2.pdf", devs1)
          devs1 = gsub(".pdf", "_1.pdf", devs1)
          devs1 = c(devs1, devs2)
          devs1 = sort(devs1)
      }
      devs = devs1
    } 
    fdevs = devs
    devs = list()
    for (idev in 1:length(fdevs)) {pdf(fdevs[idev]); devs[[idev]] = dev.cur()}
    on.exit(for (idev in 1:length(devs)) dev.off(devs[[idev]]))
  } else fdevs = NULL
  
  cases = matrix(NA, ncol = length(inds), nrow = length(events))
  eventMeans = list()
  evres = array(NA, dim = c(length(events), length(inds), length(stats), 20, length(weeks)))
  if (missing(yranges)) yranges = list()
  # Loop over the different activity types
  for (ia in 1:length(events)) {
    atyp = events[[ia]]
    eventMeans[[ia]] = list()
    # Loop over the different indices
    for (iind in 1:length(allvar)) {
      ind = inds[iind]
      allv = allvar[[ind]]
      allv = allv[allv[, EVcol] %in% atyp,]
      if (is.null(allv) || dim(allv)[1] == 0) next
      cases[ia, iind] = max(table(allv$WEEK))
      
      # Compute mean and standard deviations for a signal/activity type
      evMean = signalMean(allv, stats = stats, events = events, first = first,
                           dels = dels, weighted = weighted,
                           weeks = weeks, week0 = week0, weekcorrect = weekcorrect, plotit = plotit,
                           plotCumsum = plotCumsum, sepPlots = sepPlots,
                           devs = devs, zeroshift = zeroshift, FOIinfo = FOIinfo,
                           legend = legend, addNum = addNum,                           
                           main = c(paste(atyp, collapse = " "), paste(cases[ia, iind])),
                           ylab = inds[iind], yrange = yranges[[ind]], ind = inds[iind])  
      
      if (!is.null(evMean$evres)) {
        eventMeans[[ia]][[iind]] = evMean$evMean
        # Store the results in evres
        evres[ia, iind, ,1:4 , ] = evMean$evres
        yranges[[ind]] = evMean$yrange
      }
      #' @importFrom utils setTxtProgressBar
      if (interactive()) setTxtProgressBar(pb, (ia-1)*length(allvar) + iind)
    }
  }
  dim4 = c("mean", "cumsum", "std", "stdcumsum", "posmean", 
           "poscumsum", "p0", "pT", "p0c", "pTc",
           "maxp0", "maxpT", "relBest", "relworst", "niu1",
           "niu2", "niu3", "niu4", "niu5", "niu6")
  dimnames(evres) = list(events, inds, stats, dim4, weeks )
  if (drop && dim(evres)[1] == 1) evres = evres[1,,,,]
  list(evres = evres, cases = cases, yranges = yranges)
}
