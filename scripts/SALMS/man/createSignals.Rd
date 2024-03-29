% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/createSignals.R
\name{createSignals}
\alias{createSignals}
\title{Function creating activity centred time series}
\usage{
createSignals(
  FOIinfo,
  nweeks,
  iyear,
  plotit,
  plotAllStats = FALSE,
  tsdir,
  piddir,
  odir,
  IDcol,
  EVDcol,
  cloudinds,
  sbss = c("s2", "s2_idx", "s1_coh6", "s1_bs", "s1_bsidx"),
  obands,
  stats,
  idxs = 1:5,
  iprint = 1
)
}
\arguments{
\item{FOIinfo}{\code{\link{data.frame}} with information about activities and the corresponding FOIs. See details}

\item{nweeks}{How many weeks to include before and after the activity?
The length of the time centred time series,  will be \code{2*nweeks + 1}}

\item{iyear}{What is the year of the data set}

\item{plotit}{Logical; should plots be generated?}

\item{plotAllStats}{Logical; if FALSE only the quantiles and the mean will be plotted}

\item{tsdir}{The name of the directory where extracted time series can be found}

\item{piddir}{Directory name where pid-files can be found (as downloaded from creodias). If missing,
data will be taken from FOIinfo}

\item{odir}{The directory of the activity centred time series}

\item{IDcol}{If the id-column is not named "ID", "FIELD_ID" or "PSEUDO_ID", the column number of the id should be given}

\item{EVDcol}{If the Event date column is not named "EVENT_START_DATE", "EVENT.1.DATE", "EVENT_DATE" or "ACTIVITY_DATE",
the column number should be given}

\item{cloudinds}{Which numbers from the Scene Classification Legend should lead to discarding of a chip
(https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm)}

\item{sbss}{Which group(s) of indices to produce (should currently not be modified)}

\item{obands}{A list of output bands, grouped according to sbss, if missing, the default bands are used}

\item{stats}{The statistical descriptors}

\item{idxs}{Which of the index group(s) in sbss to actually create}

\item{iprint}{Gives the amount of output to be printed to the console: 0 - nothing; 1 - normal; 2 - additional
output. The last one is mainly for debugging purposes, consult the code for
understanding of the output.}
}
\value{
The function will create a series of activity centred .csv files in the
\code{odir} directory. The files will be named according to the band name,
and include the weekly averaged signal values for all FOIs.
The content will be quite similar to the input, with some additional columns:
\itemize{
\item{EVENT_TYPE: This column is necessary if there is more than one
activity type in the data set}
\item{WEEK: The week number of the observation relative to the start
of the activity centred time series}
\item{DOY: Which day of the year the activity happened}
}
}
\description{
Function creating activity centred time series
}
\details{
The \code{FOIinfo data.frame} should contain an overview of the activities
for all FOIs of interest. Some columns and names are necessary (also lower case accepted):
\itemize{
\item{ID: The ID of the FOIs (the function also accepts "PSEUDO_ID" or "FIELD_ID")}
\item{EVENT_DATE: When did the activity happen (or start)? Also "ACTIVITY_DATE" or
"EVENT_START_DATE" are accepted names}
\item{EVENT_TYPE: This column should have a code for each type of activites that
should be analysed}}

The .csv-files with time series should be stored in a single directory, for each area of interest and for
each group of remote sensing signals/indicators. These files should have names
according to their content. The intention is to include more flexibility regarding names, but for
the moment, the time series need to have names reflecting their content based on Sentinel-1 and Sentinel-2.

Five different file names are expected (where ID is the ID of the FOI, the same as the ID of the \code{FOIinfo} object above:

\itemize{
\item{ID_s1_coh6_ts.csv: The different time series for the coherence (including ratios between orbits)}
\item{ID_s1_bs_ts.csv: The different time series for the back scatter (including ratios between orbits)}
\item{ID_s2_ts.csv: The different time series for S2-bands}
\item{ID_s2_idx.csv: The different time series for different derived S2-indicators}
\item{ID_s1_bsidx.csv: The different time series for indicators derived from the backscatter}
}

All these time series need some particular columns for the function \code{createSignals} to be able to
create the activity centred time series:

\itemize{
\item{Date: The date (and time) of the acquisition. This date might be an average for example for
s1_coherence signals that are averages of different orbits, and maybe also
different polarizations. Ideally, these data sets should already also include
the \code{week} column, which identifies the week of the year of the observations}
\item{Week: This column is optional, but should be available for data sets that already
include weekly averaged signals, such as averages of different polarizations and
orbits.}
\item{Band: One file can include many different bands, and this column should include the band
name for each observation. }
\item{Orbit: This one is only relevant for S1-signals. It can be omitted if the orbit can be
found from the date (if it also includes the time of the acquisition).}
\item{Count: This is optional, and only necessary if the analyses should use a weighting factor
(\code{weighted = TRUE}) in the analyses }
\item{Descriptors: The remaining columns should have the time series for the different descriptors,
with the name of each descriptor as column name.}
}
}
\examples{
# Output to tempdir, change to something local for easier access to the 
# files and pdfs
bdir = hdir = tempdir()
ddir = system.file("extdata", package = "SALMS")
FOIinfo = read.csv(paste0(ddir, "/gtdir/FOIinfo.csv"))
tsdir = paste0(ddir, "/tsdir")
odir = paste0(bdir, "/signals")
if (!dir.exists(odir)) dir.create(odir)
pdf(paste0(hdir, "/sigCreate.pdf"))
iyear = 2020
createSignals(FOIinfo, nweeks = 7, iyear, plotit = TRUE, tsdir = tsdir, odir = odir, 
              iprint = 0, idxs = 1:5) 
dev.off()

}
\references{
{
\insertRef{Zielinski2022}{SALMS}
}
}
