



#' Function to read activity centred signals from .csv-files and store them in a list
#'
#'
#' @eval salmsparam("odir")
#' @eval salmsparam("stats")
#' @param zeroshift Logical; whether the weekly centred time series should be shifted according to the value of week0
#' @eval salmsparam("week0u") 
#'
#' @details The function reads .csv files from the directory \\code{odir}
#' The files should have the name of the signal. The column names should 
#' be what is typically produced from \\code{\\link{createSignals}}
#'
#' \\code{week0} should only be set if also \\code{zeroshift = TRUE}.
#'
#' @export
readSignals = function(odir, stats, zeroshift = FALSE, week0 = 7) {
  olddir = getwd()
  setwd(odir)
  on.exit(setwd(olddir))
  inds = list.files()
  if (missing(stats)) stats = bnms   
  inds = gsub(".csv", "", inds)
  if ("X1" %in% inds) inds = inds[-which(inds == "X1")]
  allvar = list()
  for (iind in 1:length(inds)) {
    ind = inds[iind]
    dat = read.csv(paste0(ind, ".csv"))
    IDcols = c("ID", "FIELD_ID", "PSEUDO_ID", "PSEUDO_ID.")
    IDcol = which(toupper(names(dat)) %in% toupper(IDcols))
    if (!("ID" %in% names(dat)) & length(IDcol) > 0) dat$ID = dat[,IDcol[1]]
    dat$ID = gsub(" ", "", dat$ID)
    if ("X" %in% names(dat)) dat = dat[,-which(names(dat) == "X")]
    if ("ACTIVITY_TYPE" %in% names(dat) & !"EVENT_TYPE" %in% names(dat)) 
      dat$EVENT_TYPE = dat$ACTIVITY_TYPE
    dat$EVENT_TYPE = gsub("     ", "", dat$EVENT_TYPE)
    dat$EVENT_TYPE = gsub(".0000000", "", dat$EVENT_TYPE)
    if ("VALID_OBS" %in% names(dat)) dat = dat[dat$VALID_OBS == 1, ]
    dat = dat[abs(dat$MEAN) > 1e-6, ]
    
    if (zeroshift) {   #  & length(grep("s1_coh6", ind)) + length(grep("s1_bs", ind)) > 0) {
      if (!"VALID_OBS" %in% names(dat)) dat$VALID_OBS = 1
      for (iparc in unique(dat$ID)) {
        ldat = dat[dat$ID == iparc,]
        for (iday in unique(ldat$DOY)) {
          lldat = ldat[ldat$DOY == iday, ]
          for (cstat in stats) {
            zero = lldat[lldat$WEEK == week0, cstat]
            if (length(zero) == 0) {
              dat$VALID_OBS[dat$ID == iparc & dat$DOY == iday] = 0
            } else {
            dat[dat$ID == iparc & dat$DOY == iday, cstat] = dat[dat$ID == iparc & dat$DOY == iday, cstat] - zero 
            }
          }
          
        }
      }
      nonvalid = which(dat$VALID_OBS == 0)
      if (length(nonvalid) > 0) dat = dat[-nonvalid, ]
    }
#    names(dat) = toupper(names(dat))
    allvar[[ind]] = dat
  }
  allvar
}



