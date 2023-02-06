
# Function plotting mean and confidence bands
# Currently not exported
plotConfidence = function(obs, comp, stdobs, weeks, week0, quants, ylim, xlab = "", ylab = "", 
                          main = "", addLegend = TRUE) {
  
# remove data if std is NA
  narem = which(is.na(stdobs))
  if (length(narem) > 0) {
    obs = obs[-narem]
    stdobs = stdobs[-narem]
    weeks = weeks[-narem]
  }

  if (missing(quants)) quants =  c(0.025, 0.05, 0.1, 0.2, 0.4)
  
  # Create a matrix and an array for the data and the plotting positions 
  fplot = matrix(NA, nrow = 2*length(weeks), ncol = length(quants))
  xEPSplot <-c(weeks-week0,rev(weeks-week0))
  cvals = matrix(NA, nrow = length(weeks), ncol = 2)
  for (iq in 1:length(quants)) {
    for (iday in 1:length(obs)) {
      xval = obs[iday]
      std = stdobs[iday]
      fplot[iday, iq] = qnorm(quants[iq], xval, std)
      fplot[2*length(weeks) - iday + 1,iq] = qnorm(1-quants[iq], xval, std)
      if (iq == 1) {
        cvals[iday,1] = fplot[iday, iq]
        cvals[iday,2] = fplot[2*length(weeks) - iday + 1,iq]
      }
    }
  }
  
  
  if (sum(is.na(fplot[,1])) == dim(fplot)[1]) {
    plot(1,1,main = main)
    return(0)
  } 
  
  hnM = length(quants)
  if (missing(ylim) | sum(is.na(ylim)) > 0) stop() #ylim = c(min(fplot), max(fplot))
  plot(weeks-week0, obs, ylim = ylim, col = "black", 
       pch = 16, xlab = xlab, ylab = ylab, main = main, cex = 1)
  
  cols = gray(c(0.9, 0.7, 0.5, 0.4, 0.3))
  
  for(mem in 1:length(quants)){
    # Use colors instead of B/W
    #    cc = col2alpha(hsv(h = 210/360, s = (mem/hnM), v = 1),0.3)
    #    cc = gray(0.25/mem)
    #    cols[mem] = cc
    cc = cols[mem]
    polygon(xEPSplot, fplot[,mem], col=cc, border = NA )
  }
  points(weeks-week0, obs, ylim = c(min(fplot), max(fplot)), col = "black", 
         pch = 16, cex = 1)
  lcor = findQuad(cvals, week0, weeks, ylim)
  lines(weeks - week0, rep(0.1, length = length(weeks)), lty = 2)
  
  qq = data.frame(quants, q2 = NA)
  for (iq in 1:length(quants)) qq[iq,2] = paste(quants[iq], "-", 1-quants[iq]) 
  if (addLegend) legend(lcor[1], lcor[2], legend = qq[,2], col = cols, lwd = 8, lty = 1, cex = .7,
                        title = "Uncertainty bands")
  lines(weeks-week0, obs, col = "black")
  return(ylim)
}


findQuad = function(df, week0, weeks, yrang) {
  if (missing(weeks)) weeks = 1:dim(df)[1]
  if (missing(yrang)) yrang = range(df, na.rm = TRUE)
  
  ydiff = abs(diff(yrang))
  qs = abs(yrang[2]-max(df[weeks < week0, ], na.rm = TRUE))/ydiff
  qs[2] = abs(yrang[2]-max(df[weeks > week0, ], na.rm = TRUE))/ydiff
  qs[3] = abs(min(df[weeks < week0, ], na.rm = TRUE)-yrang[1])/ydiff
  qs[4] = abs(min(df[weeks > week0, ], na.rm = TRUE)-yrang[1])/ydiff
  qi = which.max(qs)
  if (qi %in%  c(1,2)) {
    ycor = yrang[2]-0.05*ydiff
  } else if (qi == 3) {
    ycor =  min(df[weeks < week0,1])
  } else if (qi == 4) {
    ycor = min(df[weeks > week0,1])
  } else stop("findQuad - something wrong")
  c(if (qi %in% c(1,3)) weeks[1] else weeks[floor(0.8*length(weeks))], ycor)
}

if (FALSE) {
  cc = NA
  for (i in 1:5) cc[i] = col2alpha(hsv(h = 210/360, s = (i/5), v = 1),0.3)
  for (i in 1:5) cc[i] = gray(1/i/2+0.3)
  cc = gray(c(0.9, 0.7, 0.5, 0.4, 0.3))
  plot(1:10, 1:10, t = "l", lwd = 10, col = cc[1])
  for(mem in 2:5){
    lines(1:10, seq(mem, 10-mem, length.out = 10 ), col = cc[mem], lwd = 10)
    #  lines(1:10, seq(mem+0.5, 10-mem-1, length.out = 10 ), col = cc[mem], lwd = 10)
    #  lines(1:10, seq(10-mem/2, mem/2, length.out = 10 ), col = cc[mem], lwd = 10)
  }
}
