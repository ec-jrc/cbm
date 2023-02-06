#' Create means of signal functions for an activity type
#' 
#' The function computes mean and standard deviation for a particular 
#' activity type, for the statistics included in the stats variable.
#' 
#' 
#' @eval salmsparam("dat")
#' @eval salmsparam("stats")
#' @param events If only a certain type of events in \code{dat} should be used
#' @param first Logical; TRUE if only the first event of the year of each 
#' FOI should be included.
#' @param dels The minimum number of days (or a vector of minimum number of days) between two activities for 
#' one of them to be included in the mean.
#' @param weighted Logical; TRUE if the mean should be weighted according 
#' to the number of acquisitions used for the weekly mean.
#' @param weeks The number of weeks used for the signal, taken as all values of 
#'   \code{dat$WEEK} if missing. Only necessary if \code{plotit = TRUE}
#' @eval salmsparam("week0u")
#' @eval salmsparam("weekcorrect")
#' @param plotit Should the function plot anything? Either "confidence", "extra"
#'   or "both"/TRUE for all plots.
#' @param plotCumsum Should also the cumulative sum (before/after week0) be plotted?
#' @eval salmsparam("devsMean")
#' @eval salmsparam("sepPlots")
#' @param zeroshift Logical; should all activity centred time series be shifted according to the value at week0?
#' @eval salmsparam("xlab")
#' @eval salmsparam("ylab")
#' @eval salmsparam("main")
#' @eval salmsparam("yrange")
#' @eval salmsparam("FOIinfo")
#' @eval salmsparam("ind")
#' @eval salmsparam("EVDcol")
#' @eval salmsparam("legend")
#' @eval salmsparam("addNum")
#' @eval salmsparam("iprint")
#' 
#' @details 
#' If the means should only be computed for a particular activity
#' type, the different activity types have to be in the column
#' \code{dat$EVENT_TYPE}. The FOI IDs need to be in a column with the name 
#' \code{dat$ID}. The column names of the statistics in the data.frame 
#' need to match the list of statistics listed in \code{stats}. \cr \cr

#' The \code{dat data.frame} should include all the activity-centred weekly
#' observations for all FOIs of interest. The \code{data.frame} needs data with 
#' particular column names as a minimum (they do not have to be in the same order). 
#' The column names are not case sensitive. 
#' \itemize{
#'   \item{ID}{ - The IDs of the FOIs}
#'   \item{EVENT_TYPE}{ - This column gives a code for activity type, and should
#'     match the activities in the \code{events} argument if the function 
#'     should only operate on the activity types of that argument.}
#'   \item{WEEK}{ - The week number of the observation relative to an activity (\code{week0}).} 
#'   \item{DOY}{ - Which day of the year the activity happened. This is necessary to separate
#'               different activities at the same FOI}
#'   \item{COUNT}{ - The number of acquisitions per week, only used if 
#'     \code{weighted = TRUE}}
#'   \item{MEAN, MIN, etc}{ - The data frame must include columns with names matching the
#'     statistic descriptors in the argument \code{stats} for which calculation 
#'     is requested. \code{stats} that are not matched by a column name in \code{dat} will be
#'     ignored. }
#' }
#' 
#' @return A list of list of means, standard deviations and the y-limits used
#' in the plots (can be modified for later call of the function).
#' The list is organized as
#' \code{eventMeans[[statistic]][[iidel]]} where the statistic is the name
#' of the statistic for which a mean and std has been computed, and iidel
#' refers to which number of \code{dels}  we are looking at. If \code{dels = 0},
#' \code{iidel = 1}.
#' 
#' 
#' 
#' @references{
#'   \insertRef{Zielinski2022}{SALMS}
#' }
#'  
#' @export
signalMean = function(dat, stats, 
                       events, first = FALSE, dels = 0, weighted = FALSE,  
                       weeks, week0 = 7, weekcorrect = 0, plotit = FALSE, plotCumsum = FALSE, devs, 
                       sepPlots = NULL, zeroshift = TRUE,  
                       xlab = "weeks", ylab = "", main = "", yrange = NULL,
                       FOIinfo, ind = ind, EVDcol, legend = TRUE, addNum = TRUE,
                       iprint = 1) {
  
  # Take default stats from bands.R
  if (missing(stats)) stats = bnms
  stats = toupper(stats)
  quants =  c(0.025, 0.05, 0.1, 0.2, 0.4)
  sepBands = sepStats = NULL
  if (!is.null(sepPlots)) {
    if ("bands" %in% names(sepPlots)) sepBands = sepPlots$bands else sepBands = sepPlots
    if ("stats" %in% names(sepPlots)) sepStats = sepPlots$stats else sepStats = "P50"
  }
  
  # Make it necessary for the user to hit the return button for next plot
  # if plotting to an interactive device (screen output)
  askpar = devAskNewPage()
  if (dev.interactive()) {
    devAskNewPage(ask = TRUE)
    on.exit(devAskNewPage(ask = askpar))
  }
  
  
  if (!isFALSE(plotit) & !missing(devs) && length(devs) > 0) {
  
  # Plot legend on first page
    
    if (isTRUE(plotit) | plotit == "both")  il = 2 else il = 1
    if (length(sepPlots) > 0) {
      ddev = which(unlist(lapply(lapply(sepBands, "%in%", ind), any))) + 1
    } else ddev = NULL
    if (length(ddev) > 0) extraPlot = TRUE else extraPlot = FALSE
    if (!length(ddev) == 0 && (isTRUE(plotit) | plotit == "both")) ddev = (2*ddev-1):(ddev*2) 
    devs = devs[c(1:il, ddev)]
    
    cols = gray(c(0.9, 0.7, 0.5, 0.4, 0.3))
    qq = data.frame(quants, q2 = NA)
    if (toupper(legend) == "BEFORE") {
      for (iq in 1:length(quants)) qq[iq,2] = paste(quants[iq], "-", 1-quants[iq]) 
      for (dd in devs) {
        dev.set(dd)
        plot(1,1, xlim = c(0,1), ylim = c(0,1))
        legend(0.2, 0.8, legend = qq[,2], col = cols, lwd = 8, lty = 1, cex = .7, title = "Uncertainty bands" )
      }
  }
  }
  
  # Logical - should legend be added to the confidence plots
  pAddLegend = (is.logical(legend) && legend) | toupper(legend) == "YES" 
  
  # Try to get missing arguments from dat, define some variables
  names(dat) = toupper(names(dat))
  if (!missing(events) & "EVENT_TYPE" %in% names(dat)) dat = dat[dat$EVENT_TYPE %in% events, ]
  if (missing(weeks)) weeks = unique(dat$WEEK)
  eventMeans = list()
  evres = array(NA, dim = c(length(stats), 4, length(weeks)))
  FOIs = unique(dat$ID)
  stats = stats[which(stats %in% names(dat))]
  
  
  # Remove observations not valid (usually from clouds)
  if (!"VALID_OBS" %in% names(dat)) dat$VALID_OBS = 1
  nonvalid = which(dat$VALID_OBS == 0)
  if (length(nonvalid) > 0) dat = dat[-nonvalid, ]
  if (dim(dat)[1] == 0) return(NULL)
  
  # Shift all time series so that the value at week0 is zero
  if (zeroshift) {  
    if (missing(EVDcol)) EVDcol = getEVDcol(names(dat))
    if (is(dat[, EVDcol], "character")) dat[, EVDcol] = getDate(dat[, EVDcol])
    if (!"DOY" %in% names(dat)) dat$DOY = daydoy(as.POSIXct(dat[, EVDcol]))
    for (iparc in unique(dat$ID)) {
      ldat = dat[dat$ID == iparc,]
      for (iday in unique(ldat$DOY)) {
        lldat = ldat[ldat$DOY == iday, ]
        for (cstat in stats) {
          zero = lldat[lldat$WEEK == week0, cstat]
          if (length(zero) == 0) {
            dat$VALID_OBS[dat$ID == iparc & dat$DOY == iday] = 0
          } else {
            dat[dat$ID == iparc & dat$DOY == iday, cstat] = 
              dat[dat$ID == iparc & dat$DOY == iday, cstat] - zero 
          }
        }
        
      }
    }
    dat = dat[dat$VALID_OBS == 1,]
  }
  
  # use only the first activity of each FOI if is.TRUE(first)
  if (first) {
    for (iparc in 1:length(FOIs)) {
      parc = FOIs[iparc]
      days = sort(unique(dat$DOY[dat$ID == parc]))
      for (ii in 1:length(days)) {
        dat$eventnum[dat$ID == parc & dat$DOY == days[ii]] = ii
      }
    }
    dat = dat[dat$eventnum == 1, ]
  }
  
  # create list for yranges if not missing or null
  if (is.null(yrange)) {
    yrange = list()
  }
  
  
  
  if (!missing(FOIinfo)) {
    dat$FOIday = paste(dat$ID, dat$DOY, sep = "_")
    FOIdays = unique(dat$FOIday)
    
    # Looks for the activity column, a bit more flexibility than stated in the help file
    EVcols = c("ACTIVITY_DATE", "EVENT_DATE", "EVENT_START_DATE_")
    EVcol = which(toupper(names(FOIinfo)) %in% EVcols)
    
    # Add day of year of activity in case missing and date is given
    if (!"DOY" %in% names(FOIinfo)) {
      if ("DATE" %in% names(FOIinfo) && is(FOIinfo$DATE, "POSIXct")) {
        FOIinfo$DOY = yday(FOIinfo$DATE)
      } else {
        pdate = getDate(FOIinfo[, EVcol])
        dtype = attr(pdate, "dtype")
        FOIinfo$DOY = try(yday(pdate))
      }
    }
    
    # Some flexibility for the ID columns as well
    if (!exists("IDcol")) {
      IDcol = which(toupper(names(FOIinfo)) == "ID")
      if (length(IDcol) == 0) {
        IDcols = c("FIELD_ID", "PSEUDO_ID")
        IDcol = which(toupper(names(FOIinfo)) %in% toupper(IDcols))
        if (length(IDcol) == 0) stop("Not able to find IDcol from column names")
      }
    }
    FOIinfo$FOIday = paste(FOIinfo[,IDcol], FOIinfo$DOY, sep = "_")
  }
  
  FOIs = unique(dat$ID)
  # Find all activities of the FOI
  # This could be used in plotting, to show if the average signal might
  # be affected by other events that were near in time
  pother = NULL
  if (!missing(FOIinfo)) {
    for (iparc in 1:length(FOIs)) {
      FOI = FOIs[iparc]
      pinfo = FOIinfo[FOIinfo[,IDcol] == FOI,]
      ipd = grep(paste0(FOI, "_"), FOIdays)
      for (ii in ipd) {
        pday = FOIdays[ii]
        pinf0 = pinfo[pinfo$FOIday == pday,]
        if (dim(pinf0)[1] > 1) pinf0 = pinf0[1,]
        pinf = pinfo[pinfo$FOIday != pday,]
        if ("DATE" %in% names(FOIinfo) && is(FOIinfo$DATE, "POSIXct")) {
          pinf$week = as.numeric(difftime(pinf$DATE, pinf0$DATE, units = "days"))/7
        } else {
          pinf$week = as.numeric(difftime(getDatedtype(pinf[, EVcol], dtype),
                                          getDatedtype(pinf0[, EVcol], dtype), units = "days"))/7
          pother = rbind(pother, pinf)
        }
      }
      pother = pother[abs(pother$week) <= week0, ]
    }
  }
    
    
    # Loop over the different statistical desciptors
    for (istat in 1:length(stats)) {
      cstat = stats[istat]
      eventMeans[[cstat]] = list()
      for (iidel in 1:length(dels)) {
        ldat = dat
        idel = dels[iidel]
        
        # Do not include activities if there were other activities recorded within
        # idel days before or after the activity 
        delrange = c(-idel, idel)
        if (idel > 0) {
          if (!"VALID_OBS" %in% names(dat)) dat$VALID_OBS = 1
          for (parc in unique(ldat$ID)) {
            pdat = ldat[ldat$ID == parc, ]
            days = unique(pdat$DOY)
            for (iday in days) {
              if (any(findInterval(days - iday, c(-1e6,delrange[1],-.5,.5,delrange[2], 1e6)) %in% c(2,4))) {
                ldat$VALID_OBS[ldat$ID == parc & ldat$DOY == iday] = 0
              }
            }
          }
          ldat = ldat[ldat$VALID_OBS == 1, ]
        }
        
        # continue to next activity if the number of observations do not at least correspond
        # to a full set of observations for two activities 
        if (dim(ldat)[1] < 2*length(weeks))  next
        
        cldat = ldat
        lFOIs = unique(cldat$ID)
        for (iparc in 1:length(lFOIs)) {
          parc = lFOIs[iparc]
          pdat = cldat[cldat$ID == parc, ]
          days = unique(pdat$DOY)
          # Compute cumulative sums for activities with observations for all the surrounding weeks
          # (As missing weeks will make it impossible to create the cumulative sums)
          for (iday in days) {
            ppdat = cldat[cldat$ID == parc & cldat$DOY == iday, ]
            if (!(dim(ppdat)[1] %in% (c(1:15)*length(weeks)))) {
              if (iprint > 1) print(paste("weekdiff", ind, iparc, iday, dim(ppdat)[1]))
              ppdat[,cstat] = NA
            } else {
              ppdat[,cstat] = ppdat[,cstat] - ppdat[ppdat$WEEK == week0, cstat]
              ppdat[(week0-1):1,cstat] = cumsum(ppdat[(week0-1):1,cstat])
              ppdat[(week0+1):length(weeks),cstat] = cumsum(ppdat[(week0+1):length(weeks),cstat])
            }
            cldat[cldat$ID == parc & cldat$DOY == iday, cstat] = ppdat[,cstat]
          }
          cldat = cldat[!is.na(cldat[,cstat]), ]
        }
        
        
        
        # Compute (weighted) averages for a particular activity/signal/descriptor
        if (weighted) {
          ldat$wsum = ldat[,cstat]*ldat$COUNT
          gmean = aggregate(ldat$wsum, by = list(ldat$WEEK), sum)
          gweight = aggregate(ldat$COUNT, by = list(ldat$WEEK), sum)
          gmean$x = gmean$x/gweight$x
        } else {
          gmean = aggregate(ldat[,cstat], by = list(ldat$WEEK), mean)
          if (length(grep("s1_coh6", ind)) + length(grep("s1_bs", ind)) > 0  && dim(cldat)[1] > length(weeks)) 
            gcumsum = aggregate(cldat[,cstat], by = list(cldat$WEEK), mean) else gcumsum = NULL
        }
        
        # Store the result in evres
        evres[istat, 1, gmean$Group.1] = gmean$x
        if (!is.null(gcumsum)) evres[istat, 2, gcumsum$Group.1] = gcumsum$x
        gmed = aggregate(ldat[,cstat], by = list(ldat$WEEK), median)
        gnum = aggregate(rep(1, length(ldat[,cstat])), by = list(ldat$WEEK), sum)
        gstd = aggregate(ldat[,cstat], by = list(ldat$WEEK), sd)
        if (length(grep("s1_coh6", ind))  + length(grep("s1_bs", ind)) > 0 && dim(cldat)[1] > length(weeks)) 
          gcumsumstd = aggregate(cldat[,cstat], by = list(cldat$WEEK), sd) else gcumsumstd = NULL
        evres[istat, 3, gstd$Group.1] = gstd$x
        if (!is.null(gcumsumstd)) evres[istat, 4, gcumsumstd$Group.1] = gcumsumstd$x
        
        # All results are stored in eventMeans
        eventMeans[[cstat]][[iidel]] = list(gmean = gmean, gcumsum = gcumsum, 
                                            gcumsumstd = gcumsumstd, 
                                            gstd = gstd, gnum = gnum)
        
        # Plot different graphs
        if (isTRUE(plotit) | plotit %in% c("extra", "both"))  {
          for (iplot in 1:2) {
            if (iplot == 1 & !missing(devs)) dev.set(devs[2])
            if (iplot == 2 & !missing(devs) & extraPlot & toupper(cstat) %in% toupper(sepStats)) {
                   dev.set(devs[2*il]) 
            } else if (iplot == 2) next
            
          
          sweeks = which(ldat$WEEK %in% weeks)
          
          if (is.null(yrange[[cstat]]) & idel == 0) {
            ylim = range(c(ldat[,cstat], gmean$x), na.rm = TRUE, finite = TRUE)
            yrange[[cstat]] = ylim
          } else ylim = yrange[[cstat]]
          
          if (idel > 0) {
            levent = paste(main, cstat, idel) 
          } else {
            levent = paste(main[1], cstat, if (length(main) > 1) main[2] else NULL) 
          }
          
          if (!missing(devs) & !is.null(devs)) if (iplot == 1) dev.set(devs[2]) else dev.set(devs[2*il])
          if (isTRUE(plotit) | plotit %in% c("extra", "both")) {
            plot(weeks-week0 + weekcorrect, gmean$x[weeks], ylim = ylim, 
                 xlab = xlab, ylab = ylab, main =  levent)
            lines(weeks - week0 + weekcorrect, gmean$x[weeks])
            #          lines(weeks - week0, gmean$x[weeks], col = "red")
            abline(v = 0)
            
            lines(weeks - week0 + weekcorrect, gmed$x[weeks], col = "blue")
            if (addNum) text(gnum$Group.1 - week0  + weekcorrect, mean(range(gmean$x)), labels = gnum$x)  
            lines(weeks - week0 + weekcorrect, rep(0.1, length = length(weeks)), lty = 2)
            
            lFOIs = unique(ldat$ID)
            cols = bpy.colors(length(lFOIs))
            lldat = ldat[ldat$ID == lFOIs[1], ]
            idays = unique(lldat$DOY)
            lldat = lldat[lldat$DOY == idays[1],]
            plot(lldat$WEEK-week0 + weekcorrect, lldat[, cstat], xlim = range(ldat$WEEK-week0 + weekcorrect), ylim = ylim,  
                 main =  levent, col = cols[1], t = "l", xlab = "week", ylab = ind)
            lines(weeks - week0 + weekcorrect, rep(0.1, length = length(weeks)), lty = 2)
            
            # add a vertical line for other activities happening on the FOIs
            for (ipa in 2:length(lFOIs)) {
              lldat = ldat[ldat$ID == lFOIs[ipa],]
              lines(lldat$WEEK-week0 + weekcorrect, lldat[,cstat], col = cols[ipa])
            }
          }
          if (isTRUE(plotit) | plotit %in% c("confidence", "both")) 
            boxplot(as.formula(paste(cstat, " ~ WEEK  ")),  ldat[sweeks, ],  xlab = xlab, ylab = ylab, 
                    main = levent)
            
            if (!missing(devs) & !is.null(devs) & length(devs) > 1) {
              if (iplot == 1) dev.set(devs[1]) else dev.set(devs[il+1])
            }
            
            plotConfidence(gmean$x, stdobs = gstd$x, weeks = gmean$Group.1, 
                           week0 = week0  - weekcorrect, xlab = "week",
                           ylab = ylab, main = levent, ylim = ylim, quants = quants, addLegend = pAddLegend)
            abline(h = gmean$x[gmean$Group.1 == week0], lty = 2)
            abline(v = 0)
            abline(h = 0)
            
            # Add other events to the plot          
            if(!missing(FOIinfo) && dim(pother)[1] > 0) {
              maxpts = max(table(pother$week))
              pweeks = unique(pother$week)
              pother$yval = NA
              ysub = diff(ylim)/maxpts
              cols = c("black", "red", "green", "blue")
              for (ip in 1:length(pweeks)) {
                pother$yval[pother$week == pweeks[ip]] = (1:sum(pother$week == pweeks[ip]))*ysub+ylim[1]
              }
              for (ii in 1:dim(pother)[1]) {
                points(pother$week[ii], pother$yval[ii], pch = 16, col = cols[pother$activity_type_merge[ii]])
              }
            }
            
            if (addNum) text(gnum$Group.1-week0 + weekcorrect, mean(range(gmean$x)), labels = gnum$x)  
            
            
            if (plotCumsum & !is.null(gcumsum)) {
              plotConfidence(gcumsum$x, stdobs = gcumsumstd$x, weeks = gcumsum$Group.1, 
                             week0 = week0 - weekcorrect, xlab = "week",
                             ylab = ylab, main = levent, ylim = range(gcumsum$x) + c(-max(gcumsumstd$x), max(gcumsumstd$x)),
                             quants = quants, addLegend = pAddLegend)
              abline(v = 0)
              abline(h = 0)
            } 
          }
          
        }
        
        
      }
    }
    
    list(yrange = yrange, evres = evres, eventMeans = eventMeans)
  }