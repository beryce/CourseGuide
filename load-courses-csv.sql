
use c9;

load data local infile 'course-data.csv' 
into table courses 
fields terminated by ',' 
lines terminated by '\n'
ignore 1 rows;