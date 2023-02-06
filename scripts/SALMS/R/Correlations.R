
#' Creates and plots correlations of the signals
#' 
#' @eval salmsparam("allvar")
#' @eval salmsparam("events")
#' @eval salmsparam("inds")
#' @eval salmsparam("stats")
#' @param custom Either "ALL" or a list of different combinations of indexes
#'            to be grouped in the plots
#' @param mar The margins, as defined in \code{\link{par}}. This parameter is set explicitly 
#'            in the function if missing, as the default value is not good for 
#'            the title.
#' @param drop Should the function only return an array if there is only
#'            one activity type, instead of a list of length one
#' @param ... Other parameters to \code{\link[corrplot]{corrplot}}
#' 
#' @details 
#' The function produces different correlation plots for the individual 
#' statistical descriptors of the data set. The plots can either be sent to 
#' a file (typically multipage pdf) or to the screen, where next plots 
#' are shown after hitting the return button.
#' 
#' @returns
#' The function will return the correlations as a multidimensional array,
#' or a list of arrays if there are more than one activity type in the 
#' data set. The dimensions are length(inds), length(inds), length(descriptors)
#' 
#' 
#' @examples
#' ddir = system.file("extdata", package = "SALMS")
#' odir = paste0(ddir, "/signals")
#' allvar = readSignals(odir)
#' allcorrs = signalCorrelations(allvar, stats = c("MIN", "P50"))
#' allcorrs = signalCorrelations(allvar, stats = c("MIN", "P50"),
#'                   custom = list(first = c("B04", "B08", "NDVI", "RVI"),
#'                                 second = c("BSI", "GARI", "s1_bs_rAD", "s1_coh6")))
#' 
#' @export
signalCorrelations = function(allvar, events, inds, stats, custom = "ALL", mar = NULL,
                              drop = TRUE, ...) {

  # Set sensible plotting margins for interactive plots (default for corrplot
  #    is c(0,0,0,0))
  #' @importFrom grDevices dev.interactive
  if (is.null(mar) & dev.interactive()) mar =c(5,4,4,2)  else if (is.null(mar)) mar = c(0,0,0,0) 
  
  if (missing(inds)) inds = names(allvar)
  # Create custom plot with all indexes together if custom == "ALL"
  if (!missing(custom) && length(custom) == 1 && is.character(custom) && 
      toupper(custom) == "ALL") {
    custom = list(all = names(allvar))
  }
  if (length(custom) > 0) bands = c(bands, custom) 

  # Use default statistical descriptors if variable is missing
  if (missing(stats)) stats = bnms
  allcors = list()
  
  # Make it necessary for the user to hit the return button for next plot
  # if plotting to an interactive device (screen output)
  #' @importFrom grDevices devAskNewPage
  askpar = devAskNewPage()
  if (dev.interactive()) {
    devAskNewPage(ask = TRUE)
    on.exit(devAskNewPage(ask = askpar))
  }
  
  # Make sure to have ACTIVITY_TYPE as one of the column names 
  allvar = lapply(allvar, FUN = function(x) {names(x) = toupper(names(x)); x})
  if ("EVENT_TYPE" %in% names(allvar[[1]]) && !"ACTIVITY_TYPE" %in% names(allvar[[1]])) {
    allvar = lapply(allvar, FUN = function(x) {x$ACTIVITY_TYPE = x$EVENT_TYPE; x})
  }
  if (missing(events) & "ACTIVITY_TYPE" %in% names(allvar[[1]])) {
    events = unique(allvar[[1]]$ACTIVITY_TYPE)
  } else if (missing(events)) {
    events = 1
    allvar = lapply(allvar, FUN = function(x) {x$ACTIVITY_TYPE = 1; x})
  }
  
  # Loop over activity types and create a correlation array (corrt) 
  # and a count of the number of combinations (nummt) for each activity type
  for (ia in 1:length(events)) {
    ev = events[ia]    
    corrt = nummt = array(0, dim = c(length(allvar), length(allvar), length(stats)))
    # Loop over indexes in a matrix (iind and jind)
    for (iind in 1:(length(allvar)-1)) {
      allv = allvar[[iind]]
      if (ev != "all") allv = allv[allv$ACTIVITY_TYPE %in% ev, ]
      ipars = unique(allv$ID)
      for (jind in (iind+1):length(allvar)) {
        allw = allvar[[jind]]
        if (ev != "all") allw = allw[allw$ACTIVITY_TYPE %in% ev, ]
        # Select the same time period for the same FOI for the 
        # different indicators
        for (iparc in 1:length(ipars)) {
          parc = ipars[iparc]
          alli = allv[allv$ID == parc, ]
          allj = allw[allw$ID == parc, ]
          alli = alli[!is.na(alli[,1]),]
          allj = allj[!is.na(allj[,1]),]
          if (is.null(allj) || dim(allj)[1] == 0) next
          days = unique(alli$DOY)
          for (iday in days) {
            allii = alli[alli$DOY == iday, ]
            alljj = allj[allj$DOY == iday, ]
            if (is.null(alljj) || dim(alljj)[1] == 0) next
            allc = merge(allii, alljj, by = "WEEK") 
            if (dim(allc)[1] < 5) next
            
            for (istat in 1:length(stats)) {
              st = stats[istat]
              # Find the correlations
              # The column names of allc will be stat.x and stat.y after the merge
              # operation above
              #' @importFrom stats cor
              cc = cor(allc[,paste0(st, ".x")], allc[,paste0(st, ".y")], use = "complete")
              if (is.na(cc)) next
              corrt[iind, jind, istat] = corrt[iind, jind, istat] + cc
              nummt[iind, jind, istat] = nummt[iind, jind, istat] + 1
            }
          }
        }
        # Make the correlation matrices symmetric
        for (istat in 1:length(stats)) corrt[jind, iind, istat] = corrt[iind, jind, istat]
        for (istat in 1:length(stats)) nummt[jind, iind, istat] = nummt[iind, jind, istat]
      }
      print(paste("Creating correlation table - activity type", ia, "indicator:", iind))
    }
    
    # Divide sum of correlations by the number of pairs for each correlation, 
    # make the diagonal 1
    if (sum(nummt) == 0) next
    corrt = corrt/nummt
    for (istat in 1:length(stats)) diag(corrt[,,istat]) = 1
    
    # Set the names of the dimensions of the array
    dimnames(corrt) = list(inds, inds, stats)
    for (istat in 1:length(stats))  {  
      if ("pdf" %in% names(dev.cur())) par(mfrow = c(2,2))
      for (s1bs in names(bands)) {
        corrl = corrt[inds %in% bands[[s1bs]], inds %in% bands[[s1bs]], , drop = FALSE]
        if (dim(corrl)[1] < 2) next 
        if (dim(corrl)[1] > 15) par(mfrow = c(1,1))
        #' @importFrom corrplot corrplot 
        corrplot(corrl[,,istat], method = "square", 
                 title = paste(ev,stats[istat]), mar = mar) 
      }
      par(mfrow = c(1,1))
      corrplot(corrt[,,istat], method = "square")
      bbs = c(bands[["s2"]],bands[["idx"]])
      corrl = corrt[inds %in% bbs, inds %in% bbs, ]
      corrplot(corrl[,,istat], method = "square", 
               title = paste(ev,stats[istat])) 

    }
    print(paste("done correlation ", ia, paste(ev, collapse = " ")))
    allcors[[ia]] = corrt
  }
  if (length(allcors) == 1 & drop) allcors = allcors[[1]]
  allcors
  
}
  
  
  