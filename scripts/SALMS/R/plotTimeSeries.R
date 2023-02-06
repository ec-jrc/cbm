
#' Plotting of signal time series 
#' 
#' Function plotting the time series of signals for each FOI, for the 
#' different descriptors and bands
#' 
#' The function can take two output devices (or file names) for the plotting. 
#' In the first device, the function will first produce a plot for each descriptor, grouping together the 
#' bands for each sensor/index type (s1_coh6, S2, s1_bs, s2_idx, ...). Then it will produce plots for 
#' each band, showing all the different descriptors in the same plot. This plot will typically have a 
#' large number of pages
#' 
#' The function will produce considerably fewer pages for the second device, making it easier to 
#' look through the output. The function will only make coherence plots, for p50/median.
#'  
#' @examples
#' # Create a limited set of bands
#' bands = list(s1_coh6 = paste0("s1_coh6", c( "_VH_A",  "_VV_A")), 
#'     s2 = c("B02", "B03", "B04", "B05"), 
#'     s1_bs = paste0("s1_bs", c("_VH",  "_VH_A", "_VH_D")),
#'     s2_idx = c("NDVI", "NDWI", "NDPI", "OSAVI", "SAVI"), 
#'     s1_bsidx = c("RVI",  "CPRI"),
#'     s1_coh6rat = c("s1_coh6_VH_rAD", "s1_coh6_rADN", "s1_coh6_VV_rADN"),
#'     s1_bsrat = c("s1_bs_rAD", "s1_bs_rADN", "s1_bs_VH_rADN", "s1_bs_VV_rADN"))
#' 
#' 
#' # Directory names and file names have to be modified
#' tsdir = system.file("extdata", package = "SALMS")
#' FOIinfo = read.csv(paste0(tsdir, "/gtdir/FOIinfo.csv"))
#' tsdir = paste0(tsdir, "/tsdir")
#' hdir = tempdir() 
#' devs = list()
#' pdf(paste0(hdir, "/ts1.pdf"))
#' devs[[1]] = dev.cur()
#' pdf(paste0(hdir, "/ts2.pdf"))
#' devs[[2]] = dev.cur()
#' 
#' plotTimeSeries(FOIinfo,  devs = devs, tsdir = tsdir, obands = bands, iyear = 2020, 
#'      legend = "before") 
#' graphics.off()
#' 
#' @eval salmsparam("FOIinfo")
#' @param FOIs an array of FOI IDs to be plotted
#' @eval salmsparam("stats")
#' @eval salmsparam("plotAllStats")
#' @eval salmsparam("sepPlots")
#' @param cols array with colors
#' @eval salmsparam("obands")
#' @eval salmsparam("devs")
#' @param tsdir where to find the time series
#' @param iyear The year to plot. Can also be found from data, but will complain if there are more 
#'              than one year in the data set.
#' @eval salmsparam("yranges")
#' @param removeClouds Logical; Should clouds be removed
#' @eval salmsparam("cloudinds")
#' @param addEvent Should a vertical line be added for the events (from column EVENT_TYPE)
#' @param addText Should the line be accompanied with the event type itself
#' @eval salmsparam("legend")
#'    
#'    
#'    
#' @references{
#'   \insertRef{Zielinski2022}{SALMS}
#' }    
#'              
#' @export
plotTimeSeries = function(FOIinfo, FOIs, stats, plotAllStats = TRUE, sepPlots = NULL, 
                          cols, obands, devs, tsdir, iyear, yranges,
                          removeClouds = TRUE, cloudinds, addEvent = TRUE, 
                          addText = FALSE, legend = TRUE) {
  
  if (missing(devs)) devs = dev.cur()
  if (missing(cloudinds)) cloudinds = bcloudinds
  if (missing(FOIs)) FOIs  = unique(FOIinfo$ID)
  olddir = getwd()
  on.exit(setwd(olddir), add = TRUE)
  sepBands = sepStats = NULL
  if (!is.null(sepPlots)) {
    if ("bands" %in% names(sepPlots)) sepBands = sepPlots$bands else sepBands = sepPlots
    if ("stats" %in% names(sepPlots)) sepStats = sepPlots$stats else sepStats = "P50"
  }
  if (missing(yranges)) yranges = list()
  if (is(devs, "character")) {
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
    on.exit(for (idev in 1:length(devs)) dev.off(devs[[idev]]), add = TRUE)
  } else fdevs = NULL
  odir = getwd()
  setwd(tsdir)
  if (!missing(stats)) nms = stats else nms = bnms
  if (!plotAllStats ) nms = bnmsp[bnmsp %in% nms]
  nms = tolower(nms)
  if (missing(obands)) sabands = allbands else sabands = obands    
  if (missing(cols)) {
    cols1 = c("black", "red", "blue", "green", "brown", "purple", "orange", "yellow", "pink", "turquoise", gray(0.25), gray(0.50) )
  } else cols1 = cols
  
  

  if (toupper(legend) == "BEFORE" & !missing(devs) && length(devs) > 0) {
    for (idev in 1:length(devs)) {
      dev.set(devs[idev])
      plot(1,1, xlim = c(-0.1,1), ylim = c(0,1))
      locx = 0.05
      locy = 0.95
      nbands = names(sabands)
      for (igr in 1:length(sabands)) {
        nband = nbands[igr]
        slen = length(sabands[[nband]])
        legend(locx, locy, sabands[[nband]], col = cols1[1:slen], lty = 1)
        locy = locy-0.07*slen
        if (locy < 0.4) {
          locy = 0.95
          locx = locx + 0.25
        }
      }        
      legend(locx, locy, nms, col = cols1[1:length(nms)], lty = 1)
      
    }
  }
  
  
  if (addEvent && !"WEEK" %in% names(FOIinfo)) {
    EVDcol = which(toupper(names(FOIinfo)) %in% c("ACTIVITY_DATE", "EVENT_DATE")) 
    if (length(EVDcol) > 1) EVDcol = EVDcol[1]
    pdate = FOIinfo[, EVDcol]
    ppdate = getDate(pdate)
    FOIinfo$WEEK = wek(ppdate)
  }
  
  oyear = 0
  for (s1bs0 in names(sabands)) {
    if (is.null(yranges[[s1bs0]])) yranges[[s1bs0]] = list()
    bands = sabands[[s1bs0]]
    #      if (example == "ex" & s1bs0 == "idx") bands = "NDVI"
    if (length(grep("rat", s1bs0)) > 0) {
      s1bs = gsub("rat", "", s1bs0) 
    } else if (s1bs0 %in% c("s2_idx2", "s2_idx3", "s2_idx4")) {
      s1bs = "s2_idx"
    } else s1bs = s1bs0
    ncor = 0    
    cols = cols1[1:length(bands)]
    for (iparc in 1:length(FOIs)) {
      parc = FOIs[iparc]
      parc = gsub("/", "", parc) 
      pinfo = FOIinfo[gsub("/", "", FOIinfo$ID) == parc, ]
      names(pinfo) = toupper(names(pinfo))
      if ("AREA" %in% names(pinfo)) parea = paste0("area:", round(pinfo$AREA[1], 2)) else parea = NULL
      
      
      dat = try(read.csv(paste0(parc, "_", s1bs, "_ts.csv")) )
      if (is(dat, "try-error")) next
      if (max(table(dat$band)) <= 1) next
      names(dat) = tolower(names(dat))
      
      dbands = unique(dat$band)
      dbands = dbands[dbands %in% unlist(sabands)]
      #     if (length(grep("s1", s1bs)) > 0 & length(grep("s1", bands)) == 0) bands = paste(s1bs0, bands, sep = "_") 
      
      ## The lines below could be an issue if the date format is wrong - gives dat$date = NA, which again means year(dat$date) cannot be equal to iyear
      if ("date_part" %in% names(dat) & !("date" %in% names(dat))) { 
        dat$date = as.POSIXct(dat$date_part, origin =  "1970-01-01",tz = "GMT")
      } else if (length(grep("T", dat$date[1])) > 0) {
        dat$date = ymd_hms(dat$date)
      } else if (!is(dat$date[1], "POSIXct") & !is(dat$date[1], "Date")) {
        dat$date = getDate(dat$date)
      }
      
      if (missing(iyear)) iyear = unique(year(dat$date))
      if (length(iyear) > 1) stop(paste("more than one year in dataset", iyear, collapse = " "))
      if (iyear != oyear) {
        ydates = seq(dmy(paste0("0101", iyear)), dmy(paste0("3112", iyear)), by = 1)
        wekd = wek(ydates)
        mts = data.frame(month = c("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), w = 1)
        for (imon in 1:12) {
          ww = sprintf("15%2.2i%i", imon, iyear)
          mts$w[imon] = wekr(dmy(ww), wekd)
        }
      }
      
      if (length(grep( "s2", s1bs) ) > 0 ) {
        oodat = dat
        if (!missing(cloudinds) & !"valid_obs" %in% tolower(names(dat))) {
          dat$valid_obs = 0
          dates = unique(dat$date)
          for (idat in dates) {
            ids = which(dat$date == idat)
            ccov = sum(dat[ids, which(names(dat) %in% cloudinds) ], na.rm = TRUE)/
              sum(dat[ids, grep("hist", names(dat)) ], na.rm = TRUE)
            if (ccov < 1e-6) dat$valid_obs[ids] = 1
          }
        }
        if ("valid_obs" %in% tolower(names(dat))) dat = dat[dat$valid_obs == 1, ]
      } else if (length(grep("s1", s1bs) ) > 0 ) {
        if (!"orbit" %in% tolower(names(dat))) {
          dat$orbit = "D"
          #' @importFrom lubridate hour
          dat$orbit[lubridate::hour(dat$date) > 12] = "A"
        }
      }
      else warning("data set seems not to be Sentinel 1 or Sentinel-2")
      
      
      dat = dat[year(dat$date) %in% iyear,]
      
      if (!"week" %in% tolower(names(dat))) dat$week = wek(dat$date)
      if (!"weekr" %in% tolower(names(dat))) {
        dat$weekr = 0
        # Find the real (not integer) week of the observations
        for (iw in 1:length(dat$weekr)) dat$weekr[iw] = wekr(dat$date[iw], wekd)
      }
      dat = dat[dat$week > 2 & dat$week < 50,] # Exclude start and end of the year observations
      
      dataggr = dat
      # Make one plot for each descriptor for devs[1], putting the groups of bands together in the same plot
      for (stat in nms) {   
        if (sum(!is.na(dat[,stat])) == 0) next
        for (ipl in 1:2) {

          if (ipl == 1 & !missing(devs)) dev.set(devs[1])
          if (ipl == 2 & !missing(devs) && length(sepBands) > 0 && stat %in% sepStats) {
            ddev = which(unlist(lapply(lapply(sepBands, "%in%", bands), any))) + 1
            dev.set(devs[ddev]) 
          } else if (ipl == 2) next
          
          # Normalizing data that might not be bound by 0-1
          if (s1bs0 %in% c("idx", "idx2", "idx3", "idx4", "idxbs", "s1_rat", "bs_rat")) {
            for (iband in 1:length(dbands)) {
              lmns = stat
              for (lnm in lmns) {
                ids = which(dataggr$band == dbands[iband])
                brange = range(dataggr[ids, lnm], na.rm = TRUE)
                dataggr[ids, lnm] = (dataggr[ids, lnm]-brange[1])/(diff(brange))
              }
            }
          } 

          # Trying to get some sensible ranges if yranges are not given
          if (!is.null(yranges[[s1bs0]][[stat]])) {
            ylim = yranges[[s1bs0]][[stat]]
          } else if (s1bs == "s2" | !(stat %in% nms) ) {
            ylim = range(dat[, stat], na.rm = TRUE)
          } else if (s1bs0 == "bs") {
            ylim = c(0,0.3)
          } else  if (s1bs == "idx") {
            ylim = c(-0.5, 1) 
          } else ylim = c(0,1)
          plot(dataggr$weekr[dataggr$band == dbands[1]], dataggr[dataggr$band == dbands[1], stat], t = "l", 
               ylab = "value", xlab = "week", ylim = ylim, xlim = c(1,52), 
               cex.lab = 1.5, cex.axis = 1.4, lab = c(10, 5, 7))
          title(paste(s1bs0, parc, stat, parea), line = 2.5)
          
          for (iband in 2:length(dbands)) {
            lines(dataggr$weekr[dataggr$band == dbands[iband]], dataggr[dataggr$band == dbands[iband], stat], 
                  col = cols[iband])  
          }
          
          if ((is.logical(legend) && legend) | toupper(legend) == "YES") {
            weeks = dataggr$weekr[dataggr$band == dbands[1]]
            w0 = weeks[ceiling(length(weeks)/2)]
            lcor = findQuad(dataggr[dataggr$band %in% dbands[iband], stat, drop = FALSE], 
                            w0, weeks, yrang = ylim)
            legend(lcor[1], lcor[2], dbands, col = cols1[1:length(dbands)], lty = 1)
          }            
          

          # Remove FALSE to get dots for all the observations as well
          if (FALSE && s1bs %in% c("s2", "idx", "idx2", "idx3", "idx4")) {
            for (iband in 1:length(dbands)) points(dataggr$weekr[dataggr$band == dbands[iband]], 
                                                   dataggr[dataggr$band == dbands[iband], stat], 
                                                   col = cols[iband], pch = 16)
          }
          
          # Add the vertical lines for activities
          for (ii in 1:length(pinfo$WEEK)) {
            if (addEvent) abline(v = pinfo$WEEK[ii], col = cols[pinfo$EVENT_TYPE[ii]], lwd = 2)#5-pinfo$activity_type_merge[ii])
            if (addText) text(pinfo$WEEK[ii]+0.5, ylim[2], pinfo$EVENT_TYPE[ii])
            mcol = grep("MAGNITUDE", toupper(names(pinfo)))
            if (length(mcol) > 0) {
              if (addText) text(pinfo$WEEK[ii]+0.5, ylim[2]-0.15*pinfo$EVENT_TYPE[ii]*diff(ylim), pinfo[ii, mcol])
            }
          }

          # Add guiding lines every 0.2
          for (hh in seq(0.2, 0.8, 0.2)) abline(h = hh, lty = 2)
          axis(3,mts$w,labels=mts$month, cex.axis = 1.2) # Add months on top
          
        }
        
        # Adding more plots to dev[1]
        # Adding one plot with all the different descriptors for each band, 
        dev.set(devs[1])
        if (tolower(stat) == "p50" | tolower(stat) == "median") {
          for (iband in 1:length(dbands)) {
            band = dbands[iband]
            bids = which(dataggr$band == band)
            if (length(bids) > 0) {
              plot(dataggr$weekr[bids], dataggr[bids, nms[1]], t = "l", 
                   ylab = "value", xlab = "week", ylim = ylim, xlim = c(1,52), 
                   cex.lab = 1.5, cex.axis = 1.4, lab = c(10, 5, 7))
              title(paste(s1bs0, parc, band, parea), line = 2.5)
              
              for (lnm in 2:length(nms)) {
                lines(dataggr$weekr[bids], dataggr[bids, nms[lnm]], 
                      col = cols[lnm])  
              }
              
              if ((is.logical(legend) && legend) | toupper(legend) == "YES") {
                weeks = dataggr$weekr[dataggr$band == dbands[1]]
                w0 = weeks[ceiling(length(weeks)/2)]
                lcor = findQuad(dataggr[dataggr$band %in% dbands[iband], names(dataggr) %in% nms, drop = FALSE], 
                                w0, weeks, yrang = ylim)
                legend(lcor[1], lcor[2], nms, col = cols1[1:length(nms)], lty = 1)
              }
              
              # Add the vertical lines for activities
              for (ii in 1:length(pinfo$WEEK)) {
                if (addEvent) abline(v = pinfo$WEEK[ii], col = cols[pinfo$EVENT_TYPE[ii]], lwd = 2)#5-pinfo$activity_type_merge[ii])
                if (addText) text(pinfo$WEEK[ii]+0.5, ylim[2], pinfo$EVENT_TYPE[ii])
                mcol = grep("MAGNITUDE", toupper(names(pinfo)))
                if (length(mcol) > 0) {
                  if (addText) text(pinfo$WEEK[ii]+0.5, ylim[2]-0.15*pinfo$EVENT_TYPE[ii]*diff(ylim), pinfo[ii, mcol])
                }
              }     
              # Add guiding lines every 0.2
              for (hh in seq(0.2, 0.8, 0.2)) abline(h = hh, lty = 2)
              axis(3,mts$w,labels=mts$month, cex.axis = 1.2) # Add months on top
            }
          }
        }
        
        
        
      } # for (stat in ...)
    } # for (iparc in ...)
  }
  yranges
}


