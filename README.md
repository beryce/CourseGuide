# cs304FinalProj
This is the final project for CS304: Databases and Web Interfaces at Wellesley College. This is a web application that allows students to create reviews about particular classes and professors, in addition to accessing reviews other students have made.

#### Folders
- __sql_scripts:__ all sql files
- __templates:__ contains all htmls

#### Setting up tables

```
$ cd cs304FinalProj
$ source ../venv/bin/activate
$ mysql-ctl start
$ mysql --local-infile
mysql> source sql_scripts/make-tables.sql
mysql> source sql_scripts/load-courses-data.sql
mysql> select * from courses limit 10;
```
