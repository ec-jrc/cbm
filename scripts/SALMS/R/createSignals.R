getDate = function(date) {
  #' @importFrom lubridate ymd dmy ydm mdy
  suppressWarnings(ppdate <- ymd_hms(date)); dtype = "ymd_hms"
  if (sum(is.na(ppdate)) > 0) { suppressWarnings(ppdate <- mdy(date, tz = "UTC")); dtype = "mdy"}
  if (sum(is.na(ppdate)) > 0) { suppressWarnings(ppdate <- ymd(date, tz = "UTC")); dtype = "ymd"}
  if (sum(is.na(ppdate)) > 0) { suppressWarnings(ppdate <- dmy(date, tz = "UTC")); dtype = "dmy"}
  if (sum(is.na(ppdate)) > 0) { suppressWarnings(ppdate <- ydm(date, tz = "UTC")); dtype = "ydm"}
  attr(ppdate, "dtype") = dtype
  ppdate
}

getDatedtype = function(date, dtype) {
  #' @importFrom lubridate ydm_hms
  ppdate = switch(dtype, 
                  mdy = mdy(date, tz = "UTC"),
                  ymd = ymd(date, tz = "UTC"),
                  dmy = dmy(date, tz = "UTC"),
                  ydm = ydm(date, tz = "UTC"),
                  ydm_hms = ydm_hms(date, tz = "UTC")
  )
  ppdate
}

wekinv = function(week) {
}

wek = function(datee) {
  #' @importFrom lubridate yday
  doy = yday(datee)
  #' @importFrom insol JD 
  jd = JD(as.POSIXct(datee))
  (10 + doy - (jd - 7*((jd + 1) %/% 7)) + 2) %/% 7
  #  (10 + doy - (jd - 7*((jd + 1) %/% 7)+ 2)) %/% 7
  # (10 + doy - (jd - 7*((jd + 1)  / 7 ) + 2)) / 7
}

wek = function(datee) {
  if (!is(datee, "POSIXct")) datee = as.POSIXct(datee, tz = "UTZ")
  #' @importFrom lubridate isoweek
  isoweek(datee)
}

wekn = function(datee) {
  #' @importFrom lubridate yday
  doy = yday(datee)
  #' @importFrom insol JD 
  jd = JD(datee)
  (10 + doy -(jd - 7*((jd + 1) %/% 7) + 2)) %/% 7
}


wekr = function(datee, wekd) {
  week = wek(datee)
  doy = yday(datee)
  dw0 = min(which(wekd == week))
  week + (doy - dw0 - 3)/7
}


bandstats = function(dataggr, nms) {
  bnds = unique(dataggr$band)
  dat = dataggr[dataggr$band == bnds[1], ]
  for (nm in nms) dat[,nm] = aggregate(dataggr[,nm], by = list(dataggr$WEEK), mean)$x
  dat$band = "band_stats"
  dat
}

getEVDcol = function(pnames) {
  EVDcols = c("EVENT_START_DATE", "EVENT_START_DATE_", 
              "EVENT.1.DATE", "EVENT_DATE", "ACTIVITY_DATE")
  EVDcol = which(toupper(pnames) %in% toupper(EVDcols))
  if (length(EVDcol) == 0) stop("Not able to find EVDcol from column names")
  EVDcol
}

getEVcol = function(pnames, stop = TRUE) {
  EVcols = c("EVENT_TYPE", "ACTIVITY_TYPE")
  EVcol = which(toupper(pnames) %in% toupper(EVcols))
  if (length(EVcol) == 0 && stop) stop("Not able to find EVcol from column names")
  EVcol
}

getIDcol = function(pnames) {
  IDcols = c("ID", "PSEUDO_ID", "FIELD_ID", "PARCEL_ID", "FOI_ID")
  IDcol = which(toupper(pnames) %in% toupper(IDcols))
  if (length(IDcol) == 0) stop("Not able to find IDcol from column names")
  if (length(IDcol) > 1) {
    if ("ID" %in% toupper(pnames)) {
      IDcol = which(toupper(pnames) == "ID")
    } else IDcol = IDcol[1]
  }
  IDcol
}


#' Function creating activity centred time series 
#' 
#' 
#' 
#' 
#' @eval salmsparam("FOIinfo")
#' @param nweeks How many weeks to include before and after the activity?
#'              The length of the time centred time series,  will be \code{2*nweeks + 1}
#' @param iyear What is the year of the data set
#' @param plotit Logical; should plots be generated?
#' @eval salmsparam("plotAllStats")
#' @param tsdir The name of the directory where extracted time series can be found
#' @eval salmsparam("odir")
#' @param piddir Directory name where pid-files can be found (as downloaded from creodias). If missing, 
#'              data will be taken from FOIinfo
#' @param IDcol If the id-column is not named "ID", "FIELD_ID" or "PSEUDO_ID", the column number of the id should be given
#' @param EVDcol If the Event date column is not named "EVENT_START_DATE", "EVENT.1.DATE", "EVENT_DATE" or "ACTIVITY_DATE",
#'              the column number should be given
#' @param iprint Gives the amount of output to be printed to the console: 0 - nothing; 1 - normal; 2 - additional
#'                  output. The last one is mainly for debugging purposes, consult the code for 
#'                  understanding of the output. 
#' @param cloudinds Which numbers from the Scene Classification Legend should lead to discarding of a chip
#'                 (https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm)
#' @param sbss Which group(s) of indices to produce (should currently not be modified)
#' @param obands A list of output bands, grouped according to sbss, if missing, the default bands are used
#' @param stats The statistical descriptors
#' @param idxs Which of the index group(s) in sbss to actually create 
#' 
#' @details `r salmsdetails("FOIinfo")` 
#' 
#' @details `r salmsdetails("timeSeries")`
#' 
#' @returns `r salmsdetails("createOutput")` 
#' 
#' @references{
#'   \insertRef{Zielinski2022}{SALMS}
#' }
#' 
#' @examples 
#' # Output to tempdir, change to something local for easier access to the 
#' # files and pdfs
#' bdir = hdir = tempdir()
#' ddir = system.file("extdata", package = "SALMS")
#' FOIinfo = read.csv(paste0(ddir, "/gtdir/FOIinfo.csv"))
#' tsdir = paste0(ddir, "/tsdir")
#' odir = paste0(bdir, "/signals")
#' if (!dir.exists(odir)) dir.create(odir)
#' pdf(paste0(hdir, "/sigCreate.pdf"))
#' iyear = 2020
#' createSignals(FOIinfo, nweeks = 7, iyear, plotit = TRUE, tsdir = tsdir, odir = odir, 
#'               iprint = 0, idxs = 1:5) 
#' dev.off()
#' 
#' @export
createSignals = function(FOIinfo, nweeks, iyear, plotit, plotAllStats = FALSE, tsdir, piddir, odir, IDcol, EVDcol, 
                         cloudinds, 
                         sbss = c("s2", "s2_idx", "s1_coh6", "s1_bs", "s1_bsidx"), 
                         obands, stats, idxs = 1:5, iprint = 1) {
  if (missing(cloudinds)) cloudinds = bcloudinds
  
  # Checking if variables have been passed, or get the defaults
  if (plotit) {
    ix = 3
    iy = 3
    par(mfrow = c(3,3))
    iplot = 0
  }
  if (missing(obands)) obands = allbands
  if (!missing(stats)) nms = stats else nms = bnms
  s1bands = c(obands$s1_coh6, obands$s1_coh6rat)
  s2bands = obands$s2
  bsbands = c(obands$s1_bs, obands$s1_bsrat)
  idxbands = obands$s2_idx
  idxbsbands = obands$s1_bsidx
  if (plotAllStats) nmsp = bnms else nmsp = bnmsp
  
  if (missing(piddir)) piddir = tsdir
  NMS = toupper(nms)
  NMSP = toupper(nmsp)
  if (missing(IDcol)) IDcol = getIDcol(names(FOIinfo))
  if (missing(EVDcol)) EVDcol = getEVDcol(names(FOIinfo))
  
  dayparc = paste0(FOIinfo[,IDcol], FOIinfo[,EVDcol])
  dups = which(duplicated(dayparc))
  if (length(dups) > 0) FOIinfo = FOIinfo[-dups,]
  FOIs = unique(FOIinfo[,IDcol])
  
  if (!"DATE" %in% names(FOIinfo) || !is(FOIinfo$DATE, "POSIXct")) {
    tdate = getDate(FOIinfo[, EVDcol])
    dtype = attr(tdate, "dtype")
    FOIinfo$DATE = tdate
  }
  newinds = list()
  oyear = -999
  nopid = 0
  if (iprint > 0) print("Start generating activity centred time series")
  for (iparc in 1:length(FOIs)) {
    parc = FOIs[iparc]
    parc = gsub(" ", "", parc)
    pparc = gsub("/", "", parc) 
    if (iprint > 0) print(paste("Creating FOI:", iparc, "id: ", parc, "time:", Sys.time()))
    f1 = paste0(tsdir, "/", pparc, "_s1_coh6_ts.csv")
    f2 = paste0(tsdir, "/", pparc, "_s2_ts.csv")
    f3 = paste0(tsdir, "/", pparc, "_s1_bs_ts.csv")
    f4 = paste0(tsdir, "/", pparc, "_s2_idx_ts.csv")
    f5 = paste0(tsdir, "/", pparc, "_s1_bsidx_ts.csv")
    f6 = paste0(piddir, "/", pparc, "_pid.csv")
    #    f7 = paste0(tsdir2, "/", pparc, "_s1_rAD_ts.csv")
    #    f8 = paste0(tsdir2, "/", pparc, "_bs_rAD_ts.csv")
    
    suppressWarnings(pid <- try(read.csv(f6), silent = TRUE))
    if (1 %in% idxs) s1 = try(read.csv(f1)) else s1 = NULL
    if (2 %in% idxs) s2 = try(read.csv(f2)) else s2 = NULL
    if (3 %in% idxs) bs = try(read.csv(f3)) else bs = NULL
    if (4 %in% idxs) idx = try(read.csv(f4)) else idx = NULL
    if (5 %in% idxs) idxbs = try(read.csv(f5)) else idxbs = NULL
    
    if (!is.null(s1) & !is(s1, "try-error")) {
      if (length(grep("T", s1$date)) > 0) {
        #' @importFrom lubridate ymd_hms
        s1$date = ymd_hms(s1$date)
      } else if ("date_part" %in% names(s1)) {
        s1$date = as.POSIXct(s1$date_part, origin =  "1970-01-01",tz = "GMT")
      } else if (is(s1$date, "character")) s1$date = getDate(s1$date)
    }
    if (!is.null(s2) & !is(s2, "try-error")) {
      if (!"date" %in% names(s2)) s2$date = as.POSIXct(s2$date_part, origin =  "1970-01-01",tz = "GMT")
      if (is(s2$date, "character")) {
        s2$date = getDate(s2$date)
      }
    }
    if (!is.null(bs) & !is(bs, "try-error")) {
      if (length(grep("T", bs$date)) > 0) {
        bs$date = ymd_hms(bs$date)
      } else if ("date_part" %in% names(bs)) {
        bs$date = as.POSIXct(bs$date_part, origin =  "1970-01-01",tz = "GMT")
      } else if (is(bs$date, "character")) bs$date = getDate(bs$date)
    }
    if (!is.null(idx) & !is(idx, "try-error")) {
      if (!"date" %in% names(idx)) idx$date = as.POSIXct(idx$date_part, origin =  "1970-01-01",tz = "GMT")
      if (is(idx$date, "character")) {
        idx$date = getDate(idx$date)
      }
    }
    if (!is.null(idxbs) & !is(idxbs, "try-error")) {
      if (!"date" %in% names(idxbs)) idxbs$date = as.POSIXct(idxbs$date_part, origin =  "1970-01-01",tz = "GMT")
      if (is(idxbs$date, "character")) {
        idxbs$date = getDate(idxbs$date)
      }
    }
    
    pinfo = FOIinfo[FOIinfo[,IDcol] == parc,]
    names(pinfo) = toupper(names(pinfo))
    
    #' @importFrom lubridate year
    iyear = unique(year(pinfo$DATE))
    
    if (missing(iyear)) iyear = unique(year(pinfo$DATE))
    if (length(iyear) > 1) stop(paste("more than one year in dataset", paste(iyear, collapse = " ")))
    if (iyear != oyear) {
      ydates = seq(dmy(paste0("0101", iyear)), dmy(paste0("3112", iyear)), by = 1)
      wekd = wek(ydates)
      oyear = iyear
    }
    
    if (!is(pid, "try-error")) {
      names(pid) = toupper(names(pid))
      names(pid)[which(names(pid) == "PID")] = "ID"
    } else nopid = nopid + 1
    
    # Hard coded Sentinel-references
    for (id in idxs) {
      if (id == 1) {
        dat = s1
        bands = s1bands
        sbs = "s1"
      } else if (id %in% c(2,4)) {
        sbs = "s2"
        if (id == 2) {
          if (is(s2, "try-error")) next
          dat = s2
          bands = s2bands
        } else {
          if (is(idx, "try-error")) next
          dat = idx
          bands = idxbands
        }
        if (is(dat, "try-error")) next
        names(dat) = toupper(names(dat))
        
        if (!"VALID_OBS" %in% names(dat)) dat$VALID_OBS = 0
        if (length(grep("HIST", names(dat))) > 0) {
          for (idat in 1:dim(dat)[1]) {
            ccov = sum(dat[idat, which(names(dat) %in% toupper(cloudinds)) ], na.rm = TRUE)/
              sum(dat[idat, grep("HIST", names(dat)) ], na.rm = TRUE)
            if (ccov < 1e-6) dat$VALID_OBS[idat] = 1
          }
        }
        dat = dat[dat$VALID_OBS == 1, ]
        
      } else if (id == 3) {
        sbs = "bs"
        dat = bs
        bands = bsbands
      } else if (id == 5) {
        sbs = "bs"
        dat = idxbs
        bands = idxbsbands
      }
      names(dat) = toupper(names(dat))
      
      
      if (is(dat, "try-error")) next
      # Not really trusting any descriptor if the mean is NA
      if (sum(is.na(dat$MEAN)) > 0) dat = dat[!is.na(dat$MEAN), ]
      
      # Only work with data from iyear
      dat$YEAR = year(dat$DATE)
      iyear = as.numeric(names(sort(table(dat$YEAR), decreasing = TRUE)[1]))
      dat = dat[dat$YEAR == iyear,]
      
      # Add year if missing
      if (!"WEEK" %in% names(dat)) dat$WEEK = wek(dat$DATE)
      
      dat$WEKR = 0
      for (iw in 1:length(dat$WEKR)) dat$WEKR[iw] = wekr(dat$DATE[iw], wekd)
      dat$COUNT = 1
      if (id == 1) s1 = dat else if (id == 2) s2 = dat else if (id == 3) bs = dat
      
      dat$INUM = 1
      itest = unique(aggregate(dat$INUM, by = list(BAND = dat$BAND, WEEK = dat$WEEK), FUN = sum)$x)
      
      if (id %in% c(1,3) & !"ORBIT" %in% names(dat) & (length(itest) > 1 || itest != 1)) {
        dat$ORBIT = "D"
        #' @importFrom lubridate hour
        dat$ORBIT[lubridate::hour(dat$DATE) > 12] = "A"
        #        dat$band = gsub("c", "", dat$band)
        dat$BAND = paste(dat$BAND, dat$ORBIT, sep = "_")
      } 
      
      if (length(itest) > 1 || itest != 1) {
        dataggr = aggregate(dat$MEAN, by = list(BAND = dat$BAND, WEEK = dat$WEEK), FUN = mean)
        names(dataggr)[which(names(dataggr) == "x")] = "mean"
        
        for (nm in nms) dataggr[,nm] = aggregate(dat[,nm], by = list(BAND = dat$BAND, WEEK = dat$WEEK), mean)$x
        dataggr$NUM = aggregate(dat$COUNT, by = list(BAND = dat$BAND, WEEK = dat$WEEK), FUN = sum)$x
        
        if (id %in% c(1,3)) dataggr$ORBIT = lapply(strsplit(dataggr$BAND, "_"), "[[", 2)
      } else {
        dataggr = dat
      }
      
      if ("DATE" %in% names(FOIinfo) && is(FOIinfo$DATE, "POSIXct")) {
        evdates = pinfo$DATE
      } else {
        evdates = getDatedtype(pinfo[,EVDcol], dtype)
      }
      
      #' @importFrom insol daydoy
      days = daydoy(evdates)
      evweeks = wek(evdates)
      evweeksr = NULL
      for (iw in 1:length(evdates)) evweeksr[iw] = wekr(evdates[iw], wekd)
      evweeksallr = NULL
      if ("DATE" %in% names(FOIinfo) && is(FOIinfo$DATE, "POSIXct")) {
        evdatesall = FOIinfo$DATE
      } else {
        evdatesall = getDatedtype(FOIinfo[, EVDcol], dtype)
        for (iw in 1:length(evdatesall)) evweeksallr[iw] = wekr(evdatesall[iw], wekd)
      }
      
      pinfo$DOY = days
      pinfo$YEAR = year(evdates)
      #' @importFrom lubridate month
      pinfo$MONTH = month(evdates)
      #' @importFrom lubridate day
      pinfo$DAY = day(evdates)
      pinfo$JULIAN_DAY = JD(evdates)
      pinfo$WOY = evweeks
      
      databands = unique(dataggr$BAND)
      databands = gsub("rADn", "rADN", databands)
      
      
      lbands = databands[databands %in% bands]
      for (ib in 1:length(databands)) {
        bnew = databands[ib]
        if (id %in% c(1,3,5)) {
          bold = which(unlist(lapply(databands, FUN = function(x) length(grep(x, bnew)))) > 0)
          if (length(bold) > 1) bold = which(!is.na(match(databands, bnew)))
          # the uper version is necessary for s1-bands, the one below for indexes
        } else {
          bold = which(databands == bnew)
        }
        if (iprint > 1) print(paste("bold", bold, bnew))
        if (length(bold) > 1) stop()
        newdat = dataggr[toupper(dataggr$BAND) == toupper(databands[bold]), ]
        if (iprint > 1) print(paste("bold2", bold, bnew, paste(unique(newdat$BAND), collapse = " ")))
        if (is.null(newdat)) next
        
        for (idd in 1:length(days)) {
          iday = days[idd]
          we = evweeks[idd]
          wer = evweeksr[idd]
          evweeksallr0 = NULL
          if (!is.null(evweeksallr)) evweeksallr0 = evweeksallr - we
          if (length(we) == 0) next
          if (iprint > 1) print(paste(idd, iday, we))
          cols = c("EVENT_DATE", "EVENT_START_DATE_", "EVENT_END_DATE", "EVENT_DURATION_DAYS",
                   "EVENT_TYPE", "EVENT_MAGNITUDE", "EVENT_NUMBER", "SINGLE_FOI", "REFINED_EVENT_TYPE",
                   "YEAR_", "MONTH_", "DAY_", "JULIAN_DAY", "DOY_", "DOY", "WOY_", "WOY", "CROPCLAIME",
                   "SEQUENCE_TYPE", "ACTIVITY_TYPE", "ACTIVITY_DATE", "GT_RECORDED_DATE", "ACTIVITY_NUMBER", "AREA", "LAT",
                   "Lon", "X_COORD", "Y_COORD", "PERIMETER")
          cids = which(cols %in% names(pinfo))
          dinfo =pinfo[idd, cols[cids]]
          if (!is(pid, "try-error")) dinfo = cbind(pid, dinfo)  
          if (!"ID" %in% names(dinfo)) dinfo$ID = parc
          lda = newdat
          lda$WEEK = lda$WEEK - we
          lda = lda[abs(lda$WEEK) <= nweeks,]
          if (dim(lda)[1] == 0) next
          
          names(lda) = toupper(names(lda))
          lda$WEEK = lda$WEEK + nweeks + 1
          lda$DOY = iday
          lda$COUNT = lda$NUM
          lda$VALID_OBS = 1
          
          lda = cbind(dinfo, lda[,c("WEEK", NMS)], row.names = NULL)
          
          if (length(newinds[[bnew]]) == 0) {
            newinds[[bnew]] = lda
          } else {
            newinds[[bnew]] = rbind(newinds[[bnew]], lda)
          }
          if (iprint > 1) print(paste("before plot", iparc, parc, id, bnew, idd, length(which(newinds[[1]]$ID == FOIs[1]))))
          
          if (plotit &  id == idxs[length(idxs)] & bnew == databands[length(databands)] & iday == days[length(days)]) {
            # Fill up the page with empty plots if not all bands can be plotted on same page
            if (iplot + length(databands) > ix *iy) {
              #' @importFrom graphics plot.new
              while(!par('page')) plot.new() 
              iplot = 0
            }
            for (iband in 1:length(newinds)) {
              #' @importFrom sp bpy.colors
              cols = bpy.colors(length(nms))
              newind = newinds[[iband]]
              bname = names(newinds)[iband]
              lda = newind[newind$ID == parc & newind$DOY == iday, ]
              if (dim(lda)[1] == 0) next
              if ("ACTIVITY_TYPE" %in% names(lda) && length(unique(lda$ACTIVITY_TYPE)) > 1) {
                atypes = lda$ACTIVITY_TYPE
                lda = lda[lda$ACTIVITY_TYPE == atypes[1],]
              }
              
              plot(lda$WEEK - nweeks-1, lda$MEAN, 
                   main = paste("FOI:", parc, "DAY:", iday), ylab = bname, col = cols[1], xlab = "WEEK", 
                   ylim = range(lda[,NMS[which(NMS %in% c("MIN", "MAX"))]], na.rm = TRUE))
              iplot = iplot + 1
              for (inm in c(1:length(nmsp))) {
                nm = NMSP[inm]
                lines(lda$WEEK - nweeks, lda[,nm], col = cols[inm])
              }
              
              if (length(grep("s1_coh", bname)) > 0)  {
                dat = s1 
              } else if (length(grep("bandstats", bname)) > 0) {
                dat = s2
              } else if (length(grep("bs", bname)) > 0) {
                dat = bs
              }
              newdatabands = unique(dat$band)
              bold = which(unlist(lapply(newdatabands, FUN = function(x) length(grep(x, names(newinds)[iband])))) > 0)
              if (length(bold) > 0) {
                newdatt = dat[dat$BAND == newdatabands[bold], ]
                newdatt$WEKR0 = newdatt$WEKR - wer
                points(newdatt$WEKR0, newdatt$MEAN, pch = 16, cex = 0.5, col = "red" )
              }  
              abline(v = 0)
              #           if (!is.null(evweeksallr0)) abline(v = evweeksallr0, lty = 2, col = "blue")
              abline(v = wer-we, lty = 2)
            }
          }
        }
      }
    }
  }
  if (nopid > 0 & iprint > 0) print(paste("Did not find ", nopid, " pid-files")) 
  for (bnew in names(newinds)) {
    nind = newinds[[bnew]]
    fname = paste0(odir, "/", bnew, ".csv")
    write.csv(nind, file = fname)
  }
}

