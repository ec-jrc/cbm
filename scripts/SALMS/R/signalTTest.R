#' Run a t-test of the differences between week 0 and the other weeks
#' 
#' The function runs a comparison of the indicator values between week 0 and the weeks before and after 
#' an activity. 
#' 
#'  
#' The \code{dat} data.frame needs data with particular column names for this 
#' function. The column names are not case sensitive, and the underscores 
#' in the list below can be omitted. 
#' \describe{
#'   \item{EVENT_TYPE}{This column is necessary and should include activities
#'     matching the activities in the \code{events} argument if the function 
#'     should only operate on the activity types of that argument.}
#'   \item{ID}{The ID of the FOIs}
#'   \item{MEAN}{The data frame must include columns with names matching the
#'     statistic descriptors in the argument \code{stats} for which calculation 
#'     is requested.  }
#'   \item{stats}{that is not matched by a column name in \code{dat} will be
#'     ignored. }
#'   \item{WEEK}{The week number of the observation relative to an activity.
#'     It is not necessary that the activity happens at week 0, only that all 
#'     activities happen in the same week.} 
#'   \item{DOY}{Which day of the year the activity happened}
#'   \item{COUNT}{The number of acquisitions per week, only used if 
#'     \code{weighted = TRUE}}
#' }
#' 
#' If the means should only be computed for a particular activity
#' type, the different activity types have to be in the column
#' \code{dat$EVENT_TYPE}. The FOI IDs need to be in a column with the name 
#' \code{dat$ID}. The column names of the statistics in the data.frame 
#' need to match the list of statistics listed in \code{stats}. 
#' 
#' The argument \code{sepPlots} is a way of reducing the number of pages per
#' pdf. As an example, we could set 
#' \code{sepPlots = list(p1 = c("s1_coh6", "s1_coh6_VH"), p2 = c("NDVI", "BSI"))}.
#' The function will then plot the two different coherence plots to devs\[2\] and 
#' the two S2-indexes to devs\[3\] (devs\[1\] is for all output).
#' 
#' 
#' 
#' @param dat A data.frame with FOI activity data. See description below for 
#' more information about the content.
#' @param stats A vector with the statistic descriptors of \code{dat}, 
#' for which means should be computed.
#' @param events A vector with the events under \code{dat$EVENT_TYPE} that 
#' should be included
#' @param first Boolean - TRUE if only the first event of the year of each 
#' FOI should be included.
#' @param dels a vector of minimum number of days between two activities for 
#' one of them to be included in the mean.
#' @param weighted Boolean - TRUE if the mean should be weighted according 
#' to the number of acquisitions used for the weekly mean.
#' @param weeks The number of weeks used for the signal, taken as all values of 
#'   \code{dat$WEEK} if missing. Only necessary if \code{plotit = TRUE}
#' @param week0 If a signal consists of \code{weeks}, \code{w0} describes
#'   the week of the activity
#' @eval salmsparam("weekcorrect")
#' @param plotit Boolean - should the function plot the result of the t-tests? 
#' @eval salmsparam("devsTT1")
#' @eval salmsparam("devs")
#' @eval salmsparam("sepPlots")
#' @param main The first part of the title of the plots (the statistic and the 
#'        number of days without other activities will be added to the title)
#' @eval salmsparam("ind")
#' @eval salmsparam("yrange")
#' @eval salmsparam("legend")
#' @return A list of list of means, standard deviations and the number of 
#' FOIs included in each computation.  The list is organized as
#' \code{eventMeans[[statistic]][[iidel]]} where the statistic is the name
#' of the statistic for which a mean and std has been computed, and iidel
#' refers to which number of \code{dels}  we are looking at. If \code{dels = 0},
#' \code{iidel = 1}
#' 
#' 
#' 
#'

#' @export
signalTTest = function(dat, stats, 
                       events, first = FALSE, dels = 0, weighted = FALSE, 
                       weeks, week0 = 6, weekcorrect = 0, plotit = FALSE, devs, sepPlots = NULL, 
                       main, ind = "",
                       yrange = NULL, legend = TRUE) {
  
  if (missing(stats)) stats = bnms
  stats = toupper(stats)
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
    
    # Check if any extra plots should be created (if the index is within the
    # ones in sepPlots)
    if (length(sepPlots) > 0) {
      ddev = which(unlist(lapply(lapply(sepBands, "%in%", ind), any))) + 1
    } else ddev = NULL
    if (length(ddev) > 0) extraPlot = TRUE else extraPlot = FALSE
    devs = c(devs[1],devs[ddev])
    cols = gray(c(0.9, 0.7, 0.5, 0.4, 0.3))
    # Plot legend on first page
    if (toupper(legend) == "BEFORE") {
      for (dd in devs) {
        dev.set(dd)
        plot(1,1, xlim = c(0,1), ylim = c(0,1))
        legend(0.2, 0.8, legend = c("0.02", "0.05", "0.1", "0.2", "0.5", "0.8"),
               pch = 16, col = gray(sqrt(c(0.02, 0.05, 0.1, 0.2, 0.5, 0.8))), pt.cex = 2)
      }
    }
  }
  
  # Initialize the data frame with t-test results and the y-limits
  df = NULL
  if (is.null(yrange)) {
    yrange = list()
  }
  
  # Find the column that describes the activity type, and if there, restrict only to that type of activities
  EVcol = getEVcol(names(dat), stop = FALSE)
  names(dat) = toupper(names(dat))
  if (!missing(events) & length(EVcol) > 0) dat = dat[dat[, EVcol] %in% events, ]
  
  # Extract weeks from the data if not given as argument
  if (missing(weeks)) weeks = unique(dat$WEEK)
  FOIs = unique(dat$ID)
  
  # Check if all requested statistical descriptors actually are in the data set
  astats = stats
  stats = stats[which(stats %in% names(dat))]
  if (length(stats) < length(astats)) warning(paste("some statistical descriptors not in data set, 
                                                    might lead to inconsistencies"))

  # If first is TRUE, restrict analyses only to the first activity for all FOIs
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
  
  
  dat$FOIweek = paste(dat$ID, dat$WOY, sep = "_")
  for (istat in 1:length(stats)) {
    cstat = stats[istat]
    
    for (iidel in 1:length(dels)) {
      ldat = dat
      idel = dels[iidel]
      delrange = c(-idel, idel)
      if (idel > 0) {
        if (!"VALIDOBS" %in% names(dat)) dat$VALIDOBS = 1
        for (parc in unique(ldat$ID)) {
          pdat = ldat[ldat$ID == parc, ]
          days = unique(pdat$DOY)
          for (iday in days) {
            if (any(findInterval(days - iday, c(-1e6,delrange[1],-.5,.5,delrange[2], 1e6)) %in% c(2,4))) {
              ldat$VALIDOBS[ldat$ID == parc & ldat$DOY == iday] = 0
            }
          }
        }
        ldat = ldat[ldat$VALIDOBS == 1, ]
      } 
      
      if (dim(ldat)[1] < 2*length(unique(dat$WEEK)))  next
      tab = array(NA, dim = c(max(weeks), max(weeks),4))
      for (ii in weeks[1:(length(weeks) - 1)]) {
        
        
        for (jj in (ii+1): max(weeks)) {
          if (!(ii == week0 | jj == week0)) next
          xdat = ldat[ldat$WEEK == ii, ]
          xdat = xdat[is.finite(xdat[,cstat]),]
          ydat = ldat[ldat$WEEK == jj, ]
          ydat = ydat[is.finite(ydat[,cstat]),]
          xdat = xdat[xdat$FOIweek %in% ydat$FOIweek, ]
          ydat = ydat[ydat$FOIweek %in% xdat$FOIweek, ]
          dupsx = which(duplicated(xdat$FOIweek))
          dupsy = which(duplicated(ydat$FOIweek))
          if (length(dupsx) > 0) xdat = xdat[-dupsx, ]
          if (length(dupsy) > 0)  ydat = ydat[-dupsy, ]
          
          xdat = xdat[order(xdat$FOIweek),]
          ydat = ydat[order(ydat$FOIweek),]
          
          if(dim(xdat)[1] != dim(ydat)[1]) stop("not matching xdat and ydat")
          if (!all(xdat$FOIweek == ydat$FOIweek)) stop("not matching xdat and ydat FOIweek")
          xdat = xdat[,cstat]
          ydat = ydat[,cstat]
          if (length(xdat) > 2 & length(ydat) > 2) {
            tt = t.test(xdat, ydat, paired = TRUE)
            tab[ii,jj,1] = tt$conf.int[1] 
            tab[ii,jj,2] = tt$conf.int[2]
            tab[ii,jj,3] = tt$estimate
            tab[ii,jj,4] = tt$p.value
          }
        }
      }
      nweeks = max(weeks)
      ltab = matrix(0,ncol = 4, nrow = nweeks)
      for (ii in c(1:nweeks)) {
        #     ltab[ii,] = c(tt[ii+1, ii,1], tt[ii, ii+1,1], tt[ii,ii+1,2])
        if (ii < week0) {
          ltab[ii,] = c( tab[ii, week0, 1], tab[ii, week0,  2], tab[ii, week0, 3], tab[ii, week0, 4])
        } else if (ii > week0) {
          ltab[ii,] = c(-tab[week0, ii, 1], -tab[week0, ii, 2], -tab[week0, ii, 3], tab[week0, ii, 4])
        }
      }
      df0 = data.frame(var = stats[istat], idel = idel, signif(ltab, 3))
      df0[week0,6] = 1
      df = rbind(df, df0 )
      
      if (plotit) {
        if (sum(!is.na(df0[,3:5])) > 4) {
          for (iplot in 1:2) {
              
            if (iplot == 1 & !missing(devs)) dev.set(devs[1])
            if (iplot == 2 & !missing(devs) & extraPlot & toupper(cstat) %in% toupper(sepStats)) {
              dev.set(devs[2]) 
            } else if (iplot == 2) next

            
            
            if (idel > 0) levent = paste(main, cstat, idel) else levent = 
                paste(main[1], cstat, if (length(main) > 1) main[2] else NULL) 
            
            if (!is.null(yrange[[cstat]])) {
              ylim = yrange[[cstat]]
            } else if (length(grep("s1_coh", ind)) > 0 & cstat != "STD") {
              ylim = c(-0.1, 0.2)
              # If idel > 0, the function should continue to use the previous ylim
            } else if (is.null(yrange[[cstat]]) & idel == 0) {
              ylim = range(df0[,3:5], na.rm = TRUE)    
            }
            lweeks = weeks[!is.na(df0[,6])]
            plot(weeks-week0 + weekcorrect, df0[,5], ylim = ylim, t = "l", 
                 main = levent, xlab = "week", ylab = ind)
            lines(weeks - week0 + weekcorrect, df0[,3], col = "blue")
            lines(weeks - week0 + weekcorrect, df0[,4], col = "blue")
            lcor = findQuad(df0[,3:4], week0 + weekcorrect, weeks, yrang = ylim)
            points(lweeks - week0 + weekcorrect, df0[lweeks, 5], pch = 16, 
                   col = gray((sqrt(df0[lweeks, 6]) + 0.01) * 0.99), cex = 2)
            lines(weeks - week0 + weekcorrect, rep(0.1, length = length(weeks)), lty = 2)
            
            abline(h = 0)
            abline(v = 0)
            if ((is.logical(legend) && legend) | toupper(legend) == "YES") {
              legend(lcor[1], lcor[2], legend = c("0.02", "0.05", "0.1", "0.2", "0.5", "0.8"),
                                      pch = 16, col = gray(sqrt(c(0.02, 0.05, 0.1, 0.2, 0.5, 0.8))), pt.cex = 2)
            }
          }
        }
        
      }
    }
    
    
  }
  list(df = df, yrange = yrange)
}