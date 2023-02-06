rembands = "B8A"

allbands = bands = list(s1_coh6 = paste0("s1_coh6", c("", "_VH", "_VV", "_VH_A", "_VH_D", "_VV_A", "_VV_D")), #1:4
                        s2 = c("B02", "B03", "B04", "B05", "B06", "B07", 
                                                    "B08", "B11", "B12", "B8A"), # 5:10
                        s1_bs = paste0("s1_bs", c("", "_VH", "_VV", "_VH_A", "_VH_D", "_VV_A", "_VV_D")), #11:14
#                        idx = c("BSI", "GARI", "GARI2",  "GLI",  "GNDVI", "GSAVI", "MSAVI2", 
                        s2_idx = c("BSI", "GARI", "GARI2", "EVI", "DVI","GLI",  "GNDVI", "GSAVI", "MSAVI2", 
                                        "NDVI", "NDWI", "NDPI", "OSAVI", "SAVI"),   # 15:25
                        s1_bsidx = c("RVI", "NRPB", "CPR", "CPRI"),
                        s1_coh6rat = c("s1_coh6_rAD", "s1_coh6_VH_rAD", "s1_coh6_VV_rAD", "s1_coh6_rADN", "s1_coh6_VH_rADN", "s1_coh6_VV_rADN"),
                        s1_bsrat = c("s1_bs_rAD", "s1_bs_VH_rAD", "s1_bs_VV_rAD", "s1_bs_rADN", "s1_bs_VH_rADN", "s1_bs_VV_rADN"))

if (FALSE) {            
obands = allbands
obands[["s1_bs"]] = gsub("s1_bs_", "", obands[["s1_bs"]])
obands[["s1_bs"]] = gsub("s1_bs", "", obands[["s1_bs"]])
obands[["s1_coh6"]] = gsub("s1_coh6_", "", obands[["s1_coh6"]])
obands[["s1_coh6"]] = gsub("s1_coh6", "", obands[["s1_coh6"]])
for (sbs in c("s1_coh6", "s2", "s1_bs")) obands[[sbs]] = obands[[sbs]][obands[[sbs]] != ""]
oobands = obands
}

pol = c("VH", "VV")
cbands = list()
cbands[["s1_coh6"]] = c(paste("COH6", pol, sep = "_"))
cbands[["s1_bs"]] = c(paste("BS", pol, sep = "_"))
cbands[["s2"]] = c(paste("B", c(2:8, "8A", 11, 12), sep = "_"), "SCL")
cbands[["s2"]] = c("B02", "B03", "B04", "B08", "B05", "B06", "B07", "B8A", "B11", "B12", "SCL")
ccbands = cbands


#allbands[["s2"]] = allbands[["s2"]][-which(allbands[["s2"]] == "B8A")]
#bands[["s2"]] = bands[["s2"]][-which(bands[["s2"]] == "B8A")]


  allevents = list(mowing = list("1", "1a", "1b", "1c", "1d","2","4", 
                c("1a", "1b", "1c"), c("1a", "1b")), 
                   bare_soil = list("1a", "1b", "1c", "1d","2", "3", "4", "5", "6", "7", "8", "9","10", "11",
                c("1", "1a", "1b", "1c", "10", "11"), 
                c("2", "7"),
                c("3", "8", "1d"),
                c("4", "5", "6", "9")))

allevents$mowing = list( "1c",  c("1a", "1b"))


  bnms = toupper(c("min", "p25", "p50",	"p75",	"max",	"median",	"mean",	"SE.mean",	
          "CI.mean.0.95", "var",	"std.dev",	"coef.var",	"skewness",	"skew.2SE",	
          "kurtosis",	"kurt.2SE",	"normtest.W",	"normtest.p",	"entropy"))
  bnmsp = bnms[c(1:5,7)]
  
  events = allevents
  
bcloudinds =  paste0("hist.", c(3,8:11))
  