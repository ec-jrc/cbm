
#' Probability plots for signals and descriptors
#' 
#' The function plots as a map the probability of being above zero or above 
#' a simple threshold for different
#' signals and descriptors
#' 
#' 
#' @eval salmsparam("evres")
#' @param dfs a list with significance values, the output of \\code{\\link{signalTTest}}
#' @eval salmsparam("weeks")
#' @eval salmsparam("week0u")
#' @eval salmsparam("selwks") 
#' @eval salmsparam("selstats")
#' @eval salmsparam("stats")
#' @param allstats If the argument \code{stats} includes fewer descriptors than the ones
#'       that were used for creating \code{evres}, it is recommended to include 
#'       \code{allstats} with the names of the descriptors used for \code{evres}. 
#'       If not given, the function will assume that the names are the same as in 
#'       \code{dfs}, and that their order is the same as for the default descriptors 
#'       of the package. If these assumptions are correct, the argument is not necessary.
#' @eval salmsparam("weekcorrect")
#' @eval salmsparam("events")
#' @eval salmsparam("inds")
#' @eval salmsparam("cases")
#' @param plotit Should plots be generated? If \code{TRUE} or \code{"both"}, all plots
#'       will be generated. If \code{plotit = FALSE}, no plots will be generated.
#'       Otherwise it can either be \code{"graph"} or \code{"raster"} for the two different 
#'       plot types (see details)  
#' @param devs An optional parameter for plotting devices. It is only necessary if the user 
#'       would like to split graphs and rasters in two different documents, otherwise
#'       all output will go to the active device, which can be a pdf
#' @param sortedRasters Logical - if TRUE, there will be a range of plots that are sorted 
#'        for each descriptor/week, subsequently
#' @param computeAll Show the probablities also for indexes where none of the descriptors
#'            are estimated to give a change significantly different from zero. 
#' @eval salmsparam("drop")
#' 
#' 
#' @details 
#' The function will estimate the average probabilities of the post-activity 
#' signal being above a threshold for a set of FOIs (features/areas of interest).
#' 
#' The statistical descriptors do not have to be the same as in the previous functions.
#' However, it would be the recommendation to run a set analyses with the same selection.
#' Changing the selection could be a source of errors. There is some functionality to 
#' match different selections of descriptors, but this is not fail proof.
#' 
#' The function can produce two different types of plots, in addition to returning the results.
#' It is possible to direct these plots to one or two devices, according to the value of \code{devs}
#' 
#' The first type of plots are the probability raster maps, which are plotted if \code{plotit} is \code{TRUE}, 
#' \code{"both"} or \code{"raster"}. The first set of these rasters will 
#' have the descriptors on the x-axis and the different
#' indexes on the y-axis. The second set will have the weeks on the x-axis, for a particular choice of 
#' descriptors.
#' 
#' The probability maps, particularly the first set, give an indication of which signal and 
#' which descriptor is the most suitable for a 
#' group of FOIs. A set of plots are produced. First of all, the plots show different values for 
#' p > 0 and p > M, where M is a threshold value that can be used to identify an activity. 
#' 
#' For the first set of plots with descriptors on the x-axis, there will be separate plots for 
#' each week of the \code{selwks} parameter. The week number is  
#' the number after "W" in the heading. 
#' If there are more than one group of activity types, these 
#' are given after "G". If there is only one activity type, this part of the header is dropped. 
#'
#' The next number is the highest probability in this map. The number after P indicates the 
#' maximum number of FOIs/activities that have been used for this raster. The last part 
#' depends if \code{sortedRasters = TRUE}. If yes, the function will also generate a range
#' of plots where the rasters are subsequently ordered according to the values of each 
#' individual descriptor/week. Particularly for the descriptors, this gives the opportunity
#' to compare the different descriptors with each other. The sorted rasters can be identified 
#' with "S.ind" as a part of the header, followed by the sorting variable.
#' 
#' The second group of plots are the rasters, which are plotted if \code{plotit} is \code{TRUE}, 
#' \code{"both"} or \code{"graphs"}
#' The function will also produce a set of graphs of the change of signal values and the
#' probabilities. These might be easier to interpret if \code{computeAll = TRUE}.
#' 
#' @details `r salmsdetails("evresvar")`
#' 
#' @importFrom Rdpack reprompt
#' @references{
#'   \insertRef{Zielinski2022}{SALMS}
#' }
#'
#' @returns 
#' The function will return the evres array, updated with the probabilities. The array will have 
#' 5 dimensions (four if there is only one activity type and \code{drop = TRUE}). See also details above
#' 
#' 
#' 
#  1 - mean(x)
#  2 - cumsum(x)
#  3 - std(x)
#  4 - std(cumsum(x))
#  5 - mean(x)*sign(mean(x[selwks])) (Making sure the average change after an activity is positive)
#  6 - cumsum(x)*sign(mean(x[selwks])) (Making sure the average change after an activity is positive)
#  7 - p0 - The probability of the change being larger than 0
#  8 - p01 - The probability of the change being later than a threshold
#  9 - p0c - The probability of the cumulative change being larger than 0
# 10 - p01c - The probability of the cumulative change being larger than a threshold
# 11 - max(po): # highest p0 of interesting weeks
# 12 - max(p01): # highest p01 of interesting weeks
# 13 - The value of the change relative to highest
# 14 - The value of the change relative to lowest
# 15 - The value p0 relative to the highest
# 16 - The value p0 relative to the lowest
#' 
#' 
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
#' # The function first needs the output from allSignalMeans and allSignalTTests
#' # Store all the results from the calculations in evress, which contains an 
#' # array with the means and standard deviations
#' evress = allSignalMeans(allvar, events = 1, first = FALSE, 
#'                         dels = 0, weighted = FALSE, inds = inds, weeks = 1:15, week0 = 7, 
#'                         plotit = FALSE, zeroshift = TRUE, iprint = 1)
#' evres = evress$evres
#' cases = evress$cases
#' 
#' devs = list()
#' dfs = allSignalTTests(allvar, first = FALSE, dels = 0, weighted = FALSE,
#'                      inds = inds, weeks = 1:15, 
#'                      week0 = 7, plotit = FALSE) 
#' 
#' pdf(paste0(hdir, "/sigProb.pdf"))
#' evres1 = signalProbability(evress$evres, dfs, week0 = 7, weeks = 1:15, 
#'     selwks = 9:13, selstats = "P50", weekcorrect = 0, 
#'     events = 1, inds = inds, cases = cases)
#' dev.off()
#' 
#' 
#' @export
signalProbability = function(evres, dfs, weeks = 1:15, week0 = 7, selwks = 9:12, selstats = "P50", stats, 
                             allstats, weekcorrect = 0, events, inds, cases, plotit = TRUE, devs, 
                             sortedRasters = TRUE, computeAll = FALSE, drop = TRUE) {
  
  
  # Set progress bar
  pbl = length(inds) * length(events)
  if (interactive() ) pb = txtProgressBar(1, pbl, style = 3)
  
  if (length(dim(evres)) == 4) dim(evres) = c(1, dim(evres))
  if (missing(stats)) stats = bnms
  if (!is.numeric(selstats)) selstats = which(stats %in% selstats)
  
  if (dim(evres)[3] != length(stats)) {
    allstats = unique(unlist(lapply(dfs, FUN = function(dfi) lapply(dfi, FUN = function(df) unique(df$var)))))
    allstats[order(match(allstats, bnms))] 
    istats = which(allstats %in% stats)
  } else {
    istats = 1:length(stats)
    allstats = stats
  }
  lweeks = selwks
  bestt = FALSE
  old = FALSE
  
  print("Computing probabilities")
  for (ia in 1:length(events)) {
    atyp = events[[ia]]
    #    for (selstat in selstats) {
    for (iind in 1:length(inds)) {
      if (interactive()) setTxtProgressBar(pb, (ia-1)*length(inds) + iind)
      ind = inds[iind]
      df = try(dfs[[ia]][[iind]], silent = TRUE) # This is used for significance values further down
      # Computing average change, to see if a signal is typically increasing or decreasing,
      # then changing the sign if it is decreasing. The "normal" descriptors are treated together,
      # the rest individually
      df = df[df$var %in% stats,]
      avchange = rep(NA, length(stats))
      snorm = which(stats %in% c("MIN", "P25", "P50", "P75", "MAX", "MEAN", "MEDIAN"))
      avchange[snorm] = mean(evres[ia,iind, snorm , 1, selwks], na.rm = TRUE)
      for (iavg in 1:length(stats)) {
        if (iavg %in% snorm) next
        avchange[iavg] = mean(evres[ia,iind, iavg , 1, selwks], na.rm = TRUE)
      }
      if (is.na(avchange[1])) next
      if (dim(df)[1] == length(stats)*length(weeks)) df$week = 1:length(weeks) else stop("wrong length df")
#      print(paste("estimating probabilities", ia, iind, ind))
      for (week in lweeks) {
        dfw = df[df$week == week,]
        evres[ia, iind, istats, 5, ] = evres[ia, iind, istats, 1, ]
        evres[ia, iind, istats, 6, ] = evres[ia, iind, istats, 2, ]
        for (iavg in 1:length(stats)) if (avchange[iavg] < 0) {
          evres[ia,iind,iavg  , 5, week] = -evres[ia,iind, iavg , 1, week]
          evres[ia,iind,iavg  , 6, week] = -evres[ia,iind, iavg , 2, week]
        }
        
        p0 = p01 = p0c = p01c = NA
        for (istat in 1:length(stats)) {
          stt = stats[istat]
          df0 = df[df$var == stt,]
          if (avchange[istat] < 0) df0[,5] = -df0[,5]
          # Only compute probabilities if for significant changes
          # Previous condition: sum(is.na(dfw[,6])) == 0 &&
          if (min(dfw[,6]) < 0.05 | computeAll) { 
            thresh = max(evres[ia, iind, istat, 5,selwks], na.rm = TRUE)/2
            # using 1 - p, as pnorm gives the probability of being under the threshold
            p01[istat] = 1 - pnorm(thresh, evres[ia, iind, istat, 5, week], evres[ia, iind,istat , 3,week])
            p0[istat] = 1 - pnorm(0, evres[ia, iind, istat, 5, week], evres[ia, iind,istat , 3,week])
            p01c[istat] = 1 - pnorm(thresh, evres[ia, iind, istat, 6, week], evres[ia, iind,istat , 4, week])
            p0c[istat] = 1 - pnorm(0, evres[ia, iind, istat, 6, week], evres[ia, iind,istat , 4, week])
          } else {
            p01[istat] = p0[istat] = p01c[istat] = p0c[istat] = NA
          }
        }
        if (sum(!is.na(p0)) == 0) next
        
        # The probabilities of the signal being above the thresholds (zero and df/2)
        evres[ia, iind, istats, 7 , week] = p0  
        evres[ia, iind, istats, 8 , week] = p01 
        evres[ia, iind, istats, 9 , week] = p0c  
        evres[ia, iind, istats, 10 , week] = p01c 
        
      }
    }
  }
  # Find the highest probabilities:
  # For all the weeks With descriptors on the x-axis
  # For all the descriptors with weeks on the x-axis╩ 
  evl = 1:length(events)
  evres[evl,,istats,11,9] = suppressWarnings(apply(evres[,,istats,7,lweeks, drop = FALSE], c(1:3), na.rm = TRUE, max) )
  evres[evl,,istats,12,9] = suppressWarnings(apply(evres[,,istats,8,lweeks, drop = FALSE], c(1:3), na.rm = TRUE, max)) 

  
  
  
  # Plot raster maps of the probabilities
  if (plotit || plotit == "both" || plotit == "raster") {
    
    print(" ")
    print("plotting raster probabilities")
  if (!missing(devs)) dev.set(devs[1])
  # make rasters
  par(mar = c(5, 5, 4, 2))
  evres[!is.finite(evres)] = NA
  dimnames(evres) = list(1:dim(evres)[1], inds, allstats, 1:dim(evres)[4], weeks)
  # wst = 1: raster as function of descriptor
  # wst = 2: raster as function of lweeks
  # running in a loop, where the variables wstat, lstat, lw and stweeks can represent
  # descriptors or weeks, depending on wst
  pbl = 2*length(events)*length(selstats)
  if (interactive() ) pb = txtProgressBar(1, pbl, style = 3)
  ipbl = 0
  for (wst in 1:2) {
    if (wst == 1) wstats = lweeks else wstats = stats 
    for (ia in 1:length(events)) {
      for (selstat in selstats) {
        maxplot = TRUE
#        print(paste("Plotting raster probability maps", wst, ia, selstat))
        for (iwstat in 1:length(wstats)) {
          ipbl = ipbl + 1
          if (interactive()) setTxtProgressBar(pb, ipbl)
          
          wstat = wstats[iwstat]
          if (wst == 1) {
            lstat = 1:length(stats)    # stats
            lw = wstat                 # week
            stweeks = stats     
          } else {
            lstat = iwstat   # stats[iwstat]
            lw = lweeks      # normally 9:13
            stweeks = lw   
          }
          # Jumping to next week/descriptor if all are NA
          if (sum(!is.na(evres[ia, ,lstat , 7, lw])) == 0) next
          wmm = max(evres[ia, , lstat, 7, lw], na.rm = TRUE)
          
          # different sorting columns, the first one unsorted
          # wst decides the text and variables to be used in the header of the plots,
          # and whether to usethe selected  descriptors or weeks
          iplots = if (sortedRasters) length(stweeks)+1 else 1
          for (iplot in 1:iplots) { 
            if (wst == 1) {
              ws = "W"
              wsn = wstat
              xax = stats            
              
              selw = wstat
              sels = max(1, iplot-1)
              sortind = stweeks[iplot-1]
            } else {
              ws = "S"
              wsn = wstat
              xax = lweeks
              
              selw = lweeks[max(1, iplot-1)]
              sels = selstat
              sortind = stweeks[iplot-1]
            }
            if (iplot > 1) sind = "S.ind" else sind = ""
            porder = length(inds):1 
            cexa = if (wst == 1 & length(stats) > 10) 0.5 else 1
#            Adding activity type group to the heading if there are two or more activity groups 
            evs = if (length(events) > 1) paste("G", events[ia], collapse = " ") else ""

            # plot raster for the maximum of all weeks. Plotted for the first week available
            if (wst == 1 & maxplot) { 
              # Finding the sorting order of the raster if iplot > 1
              if (iplot > 1) porder = order(evres[ia, , sels, 11, selwks[1]], decreasing = TRUE) 
              wmh = max(evres[ia, , lstat,11,9], na.rm = TRUE)
              #' @importFrom raster raster
              rr = raster(evres[ia, porder, lstat, 11, selwks[1]])
              rnames = inds[porder[length(porder):1]]
              if (iplot == 1) {rk = rr}
              if (iplot == 4) {rorder = porder; rlstat = lstat; rsels = sels}
              
              raster::plot(rr, main = paste("Max p > 0 ", evs, "MAX P =", round(wmh, 3), "P", cases[ia, iind], 
                                           sind, sortind), 
                           axes = FALSE, zlim = c(0, 1))
              axis(1, seq(1/(length(xax)*2),1,1/length(xax)), xax, cex.axis = cexa, 
                   las = if (length(xax) > 7) 2 else 1)
              axis(2, seq(1/(length(inds)*2),1,1/length(inds)), rnames, las = 1, cex.axis = .5)
              #
              if (iplot > 1) porder = order(evres[ia, , sels, 12, selwks[1]], decreasing = TRUE) 
              wmhm = max(evres[ia, , lstat,12,9], na.rm = TRUE)
              rr = raster(evres[ia, porder, lstat, 12, selwks[1]])
              if (iplot == 1) rk2 = rr
              if (iplot == 4) rorder2 = rr
              
              # Sane as above, but for a threshold > 0
              raster::plot(rr, main = paste("Max p > M -", evs, "MAX P =", round(wmhm, 3), "P", 
                                            cases[ia, iind], sind, sortind), axes = FALSE, zlim = c(0, 1))
              axis(1, seq(1/(length(xax)*2),1,1/length(xax)), xax, cex.axis = cexa, 
                   las = if (length(xax) > 7) 2 else 1)
              axis(2, seq(1/(length(inds)*2),1,1/length(inds)), 
                   inds[porder[length(porder):1]], las = 1, cex.axis = .5, )
              if (iplot == length(stweeks)+1) maxplot = FALSE
            }            
            if (iplot > 1) porder = order(evres[ia, , sels, 7, selw], decreasing = TRUE)
            
            rr = raster(evres[ia, porder, lstat, 7, lw])
            raster::plot(rr, main = paste("p > 0 ", evs, ws, wsn, "MAX P =", round(wmm, 3), "P", 
                                          cases[ia, iind], sind, sortind), 
                         axes = FALSE, zlim = c(0, 1))
            axis(1, seq(1/(length(xax)*2),1,1/length(xax)), xax, cex.axis = cexa,
                 las = if (length(xax) > 10) 2 else 1)
            axis(2, seq(1/(length(inds)*2),1,1/length(inds)), inds[porder[length(porder):1]], las = 1, cex.axis = .5)
            
            if (iplot == 1) porder = 1:length(inds) else porder = order(evres[ia, , sels, 8, selw], decreasing = TRUE) 
            
            rr = raster(evres[ia, porder, lstat, 8, lw])
            raster::plot(rr, main = paste("p > M - ", evs, ws, wsn, "MAX P =", round(wmm, 3), "P", 
                                          cases[ia, iind], sind, sortind), axes = FALSE, zlim = c(0, 1))
            axis(1, seq(1/(length(xax)*2),1,1/length(xax)), xax, cex.axis = cexa, 
                 las = if (length(xax) > 10) 2 else 1)
            axis(2, seq(1/(length(inds)*2),1,1/length(inds)), inds[porder[length(porder):1]], las = 1, cex.axis = .5)
            
          }
        }
      }
    }
  }
  } # End raster plots
  
  
  # Graph plots
  # Creating two types of plots - with weeks on the x-axis and with the descriptors on the x-axis
  
  if (plotit || plotit == "both" || plotit == "graph") {
    if (!missing(devs) && length(devs) > 1) dev.set(devs[2])
    print(" ")
    print("plotting probability graphs")
  westat = c("stats", "weeks")
  s1bss = names(bands)
  pbl = length(events)*(length(selwks) + length(selstats))*length(s1bss)
  if (interactive() ) pb = txtProgressBar(1, pbl, style = 3)
  ipbl = 0
  for (ww in 1:2) {
    # wi is the opposite of ww - sometimes easier to work with
    wi = if (ww == 1) 2 else 1
    #' @importFrom grid grid.rect
    #' @importFrom grid gpar
    blank <- grid.rect(gp=gpar(col="white"))
    par(mfrow = c(2,2))
    
    # Four different types of plots:
    # - The value of the descriptor - in evres: ist = 1
    # - The cumulative sum of the descriptor - in evres: ist = 2
    # - The probability of the descriptor being above the threshold - in evres: ist = 7
    # - The probability of the cumulative sum of the descriptor being above the threshold 0 - in evres: ist = 9
    itypes = c("val", "cumsum", "p > 0 val", "p > 0 cumsum")
    for (ia in 1:length(events)) {
      atyp = if (length(events) > 1) paste("G", paste(events[[ia]], collapse = " ")) else ""
      # wks = 1 selects all weeks
      if (ww == 1)  wks = 1:length(selstats) else wks = selwks

      # Jump to next if all values for an event type are zero
      if (sum(!is.na(evres[ia,,,,])) == 0) {
        ipbl = ipbl + length(wks)*length(s1bss)        
        next
      }
      
      # wks is either weeks or descriptors here
      for (week in wks) {
        if (ww == 1)    selstat = selstats[week]
        for (isb in 1:length(s1bss)) {
          ipbl = ipbl + 1
          if (interactive()) setTxtProgressBar(pb, ipbl)
          
          s1bs = s1bss[isb]
          gglist = list()
          # The location in the fourth dimension of evres of the different types
          isttypes = c(1,2,7,9)
          # evres[ia, iind, stat, ist, week]
          for (ist in 1:length(itypes)) {
            jist = isttypes[ist]
            # Descriptors on the x-axis for ww = 2
            if (ww == 2) {
              sel = as.data.frame(t(evres[ia, , , jist, week ]))
              sel = sel[1:length(stats),]
              row.names(sel)[1:length(stats)] = stats
            } else {
              # Weeks on the x-axis
              sel = as.data.frame(t(evres[ia, , selstat, jist, ]))
              row.names(sel) = weeks
            }
            
            if (sum(!is.na(sel)) == 0) next
            names(sel) = inds
            
            sel1 = sel[, names(sel) %in% bands[[s1bs]], drop = FALSE]
            if (s1bs == "idx") {
              # Removing these as their values are "off the chart" when plotted together with the other ones
              remcol = which(names(sel1) %in% c("DVI", "GARI", "GARI2"))
              if (length(remcol) > 0) sel1 = sel1[,-remcol]
            }
            
            if (sum(!is.na(sel1)) == 0 | (ww == 1 && sum(!is.na(sel1[-week0,])) == 0)) next
            # Reshaping the probability matrix to long format
            selr = reshape(sel1, idvar = westat[wi], ids = row.names(sel1), times = names(sel1),
                           timevar = "band", varying = list(names(sel1)), direction = "long", v.names = s1bs)
            
            cols = bpy.colors(length(unique(selr$band)))
            
            ylim = NULL
            if (ist %in%  c(3,4)) ylim = c(min(selr[, s1bs])-0.03, 1) 
            if (length(grep("s1_coh6", s1bs)) > 0) {
              if (ist == 1) ylim = c(-.2, .4) else if (ist == 2) ylim = c(-1,2)
            }
            if (ww == 1) {
              selr$weeks = as.numeric(weeks)
              labs = as.character(weeks-week0 + weekcorrect)
            } else {
              lss = length(stats)
              selr$stats = 1:lss
              labs = stats[1:lss]
            }
#            print(paste("signalProbability graphs", if (ww == 1) "stat" else "week", week, "event", ia, s1bs))
            # Plotting the results
            #' @importFrom ggplot2 ggplot geom_vline aes_string scale_colour_manual ggtitle scale_x_continuous
            #' @importFrom ggplot2 ylim xlim element_text geom_line theme
            selr = selr[!is.na(selr[,2]), ]
            gglist[[ist]] = ggplot(selr, aes_string(westat[wi], s1bs, colour = "band")) + 
              geom_line() +
              scale_colour_manual(values = cols)   + 
              ggtitle(paste(atyp, if(ww == 1) paste("S", stats[selstat]) else paste("W", week), 
                            itypes[ist], max(cases[ia, ], na.rm = TRUE))) + 
              scale_x_continuous(breaks = 1:length(labs), labels = labs) +
              theme(axis.text.x = element_text(size = 8, vjust = .025,
                                               angle= if (ww == 2 & length(labs) > 5) 90 else 0))
            if (!is.null(ylim)) gglist[[ist]] = gglist[[ist]] + ylim(ylim)
            if (ww == 2) gglist[[ist]] = gglist[[ist]] + geom_vline(xintercept = 0)
          }
          if (length(gglist) > 0) {
            for (ist in 1:4) if (is(try(gglist[[ist]], silent = TRUE), "try-error") || is.null(gglist[[ist]])) {
              gglist[[ist]] = blank
              #          print(paste("No figure for week", week, s1bs, ist))
            }
            #' @importFrom gridExtra grid.arrange
            grid.arrange(gglist[[1]],gglist[[2]], gglist[[3]], gglist[[4]], ncol = 2, nrow = 2 )
          }
        }
        
      } 
    }
    
  }
  } # End graph plots
  print(" ")
  if (drop && dim(evres)[1] == 1) evres = evres[1,,,,]
  evres
}

