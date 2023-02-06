#' Function that ranks the probabilities of different statistical descriptors of 
#' a signal being above a threshold
#'
#' @eval salmsparam("events")
#' @eval salmsparam("inds")
#' @eval salmsparam("evres")
#' @eval salmsparam("stats")
#' @eval salmsparam("week0")
#' @eval salmsparam("weeks")
#' @eval salmsparam("selwks") 
#'
#' @details 
#' The function summarizes descriptors for all signals (ranks the best and worst)
#' for the selected
#' weeks (\code{selwks}). This selection is done based on the probability of the signal
#' being above zero for the selected weeks. 
#' This can be used as an indication of which descriptor is the 
#' most and least reliable. Additionally, it summarizes what can be regarded as optimal descriptors, 
#' i.e., summarizing the three best descriptors for each signal. This is done, as it can sometimes
#' be minor differences between the best and the second best signals. 
#' 
#' @details `r salmsdetails("evresvar")`
#' 
#' @returns 
#' The function will return a \code{data.frame} with a column for each descriptor
#' with ranking. 
#'  
#' 
#'
#' @export
optimalSignal = function(events, inds, evres, stats, week0 = 7, weeks = 1:15, 
                       selwks = 10:11) {
  if (length(dim(evres)) == 4) dim(evres) = c(1, dim(evres))
  if (missing(stats)) stats = bnms
  bbls = list()
  best = array(NA, dim = c(length(events), length(inds), length(weeks), 4))
  worst = best
  good = array(0, dim = c(length(events), length(inds), length(weeks), length(stats), 4))
  
  bbest = array(NA, dim = c(length(events), 4, length(stats) ))
  bworst = bbest
  bgood = array(NA, dim = c(length(events), 4, length(stats)))
  
  for (ia in 1:length(events)) {
    atyp = events[ia]
    for (iind in 1:length(inds)) {
      ind = inds[iind]
      
      for (week in selwks) {
        wm = which.max(evres[ia, iind, , 5, week]) 
        ww = which.min(evres[ia, iind, , 5, week]) 
        wg = order(evres[ia, iind, , 5, week], decreasing = TRUE) 

        wm1 = which.max(evres[ia, iind, , 6, week]) 
        ww1 = which.min(evres[ia, iind, , 6, week]) 
        wg1 = order(evres[ia, iind, , 6, week], decreasing = TRUE) 

        p0 = evres[ia, iind, , 7 , week]
        if (sum(!is.na(p0)) == 0) next
        p01 = evres[ia, iind, , 8 , week]
        w0 = which.max(p0)
        ww0 = which.min(p0)
        wg0 = order(p0, decreasing = TRUE)
        w01 = which.max(p01)
        ww01 = which.min(p01)
        wg01 = order(p01, decreasing = TRUE)
        
        pm0 = p0[w0]
        pm01 = p01[w01]
        ### 

        wg0 = pm0/p0
        wg01 = pm01/p01
        wg0 = p0/pm0
        wg01 = p01/pm01
        
        if (length(wm) > 0) best[ia, iind, week, 1] = wm
        if (length(w0) > 0 && pm0 > 0.7) best[ia, iind, week, 2] = w0 
        if (length(wm1) > 0) best[ia, iind, week, 3] = wm1
        if (length(w01) > 0 && pm0 > 0.7) best[ia, iind, week, 4] = w01 
        

        if (length(ww) > 0) worst[ia, iind, week, 1] = ww
        if (length(ww0) > 0) worst[ia, iind, week, 2] = ww0
        if (length(ww1) > 0) worst[ia, iind, week, 3] = ww1
        if (length(ww01) > 0) worst[ia, iind, week, 4] = ww01
        
        if (length(wm) > 0) {
          good[ia, iind, week,wg[1:3] ,1] = good[ia, iind, week,wg[1:3] ,1] +1
          good[ia, iind, week,wg[1:3] ,3] = good[ia, iind, week,wg[1:3] ,3] +1
          
          good[ia, iind, week, ,2] = good[ia, iind, week, ,2] +wg0
          good[ia, iind, week, ,4] = good[ia, iind, week, ,4] +wg01
          
        }
      }
    }
    
    for (it in 1:4) {
#      if (it > 2) itt = it+8 else itt = it
      itt = it
      tab = table(best[ia, ,selwks , itt])
      bbest[ia,it,as.numeric(dimnames(tab)[[1]])] = tab
      tab = table(worst[ia, , selwks, itt])
      bworst[ia,it,as.numeric(dimnames(tab)[[1]])] = tab
      for (istat in 1:length(stats)) bgood[ia, it, istat ] = sum(good[ia, , selwks,istat ,it ], na.rm = TRUE)
    }
  }

  dimnames(bbest)[[1]] = events
  dimnames(bbest)[[3]] = stats
  dimnames(bworst)[[1]] = events
  dimnames(bworst)[[3]] = stats
  dimnames(bgood)[[1]] = events
  dimnames(bgood)[[3]] = stats
  
  ball = list(best = bbest, worst = bworst, good = bgood)
  for (it in c(2,4)) {  # Either p > 0 or p > marker
    bbls[[it]]=list()
    mm = if (it <= 2) "p > 0" else "p > marker"
    for (lb in 1:length(ball)) {
      bbin = ball[[lb]]
      bname = names(ball)[lb]
      bbls[[it]][[lb]]=list()
      bbb = bbin[,it,]
      if (!is.matrix(bbb)) bbb = matrix(bbb, nrow = 1)
#      if (sum(is.na(bbb)) > 0) next 
      bbb = as.data.frame(bbb)
      dimnames(bbb) = list(dimnames(bbin)[[1]], dimnames(bbin)[[3]])
      bb = reshape(data.frame(idd = 1:dim(bbb)[1], as.data.frame(bbb)), idvar = "idd", direction = "long", 
                   varying = list(dimnames(bbin)[[3]]), v.names = "Count", times = dimnames(bbin)[[3]], 
                   ids = dimnames(bbin)[[1]], timevar = "P")

      
      for (ia in 1:length(events)) {
        bbl = bb[bb$idd %in% events[ia],]
        
        if (sum(bbl$Count, na.rm = TRUE) == 0) next
        bbls[[it]][[lb]]=bbl
        if (length(events) == 1) evs = "" else evs = paste(events[ia], collapse = " ")
        if (length(stats) == 6) { 
          i3 = NULL
          for (ic in bbl$P) i3 = c(i3, switch(ic, MEAN = 1, MIN = 2, P25 = 3, P50 = 4, P75 = 5, MAX = 6))
          #' @importFrom ggplot2 aes geom_bar xlab theme 
          #' @importFrom stats reorder
          print( ggplot(bbl,aes(x= reorder(P,i3),Count))+geom_bar(stat ="identity")+
                   ggtitle(paste(bname,  mm, evs)) +
                   xlab("") + theme(axis.text = element_text(size=20)))
        } else {
          
          i3 = NULL
          for (ic in bbl$P) i3 = c(i3, which(stats == ic))
          
          P = Count = "dummy"
          print( suppressWarnings(ggplot(bbl,aes(x = reorder(P, i3), Count))+geom_bar(stat ="identity")+
                   ggtitle(paste(bname, mm, evs)) +
                   xlab("") + theme(axis.text = element_text(size=20, angle = 90))))
        }
        #         
        
        #          print(ggl)
      }       
      
    }
  }
  
  
  bres = list()
  for (ii in 1:4) {
    bres[[ii]] = list()
    bres[[ii]][["be"]] = bbest[,ii,]
    bres[[ii]][["bw"]] = bworst[,ii,]
    bres[[ii]][["bg"]] = bgood[,ii,]
  }
  bord = c("be", "bw", "bg")
  bt = c("0", "0", "T", "T")
  if (!is.matrix(bres[[1]][[1]])) {
    for (ii in c(2,4)) {
      for (jj in 1:3) {
        bres[[ii]][[jj]] = data.frame(type = paste0(bord[jj], bt[ii]),matrix(bres[[ii]][[jj]], nrow = 1))
        names(bres[[ii]][[jj]]) = c("type", stats)
      }
    }
  }
  ret = suppressWarnings(do.call("rbind", do.call("rbind", bres)))  
  ret = ret[grep("b", ret$type), ]
 ret  
}
