# Possible improvements to the Outreach CbM database structure
*Just personal ideas, not all are needed/useful in this context. I use this file to keep track.*

* Always add primary keys
* If a natural primary key exists (e.g. the original parcel id defined by countries) the serial id can be removed to avoid confusion and the primary key set accordingly.
* Add foreign keys to enhance consistency and make the logical model explicit (for bulk upload they can be temporarily suppressed if really needed)
* Add indexes where required
* Same name for same column (e.g. pid/id)
* Proper data types
* Add a table to store bands name and description
* Move image metadata inside country's schemas
* Add description for tables/columns
* Create permission groups and one user per person (associated to the group)
* Correct name for geometry columns
* If parcel table for a PA is split in multiple tables for different areas of the country, the same should be done for signs and hist, but maybe keeping one single table including for parcels is the most logical solution.
* Try to harmonize (according to existing standard) the parcel tables, even if they are provided by PA in different formats. This makes sense in the Outreach DB where we have to manage many countries in the same box. PA's specific infrastructure can have their own names, data types, structure.
* Extend the structure of the database to include other tables for the additional steps of the CbM (or AMS) steps, e.g. dynamic traffic light status, even if they are not used at the moment.
* Think about solution to optimize the comparison of different parcels with the same declaration in the same area, or the same area in different years.
* Add an additional environmental layer (e.g. DEM) and use it as a "band", i.e. extract stats and feed the signs table.
