use c9;

drop table if exists posts;  -- allows us to source the batch file more than once
drop table if exists courses;  -- allows us to source the batch file more than once
drop table if exists users;  -- allows us to source the batch file more than once


CREATE TABLE users (
    name varchar(30),
    uid int auto_increment,
    hashedPW char(60),
    isAdmin enum('0', '1'),
    primary key (uid)
)

-- table constraints follow
ENGINE = InnoDB;

CREATE TABLE courses (
    name varchar(30),
    cid int auto_increment,
    semester char(3), -- ie F19, S19
    avg_rating int,
    avg_hours int,
    primary key (cid)
)
-- table constraints follow
ENGINE = InnoDB;

CREATE TABLE posts (
    pid int auto_increment,
    rating enum('1', '2', '3', '4', '5'),
    hours int not null,
    uid int not null,
    cid int not null,
    
    INDEX (uid),     -- necessary for referential integrity checking
    foreign key (uid) references users(uid)
        on update cascade
        on delete cascade,
    foreign key (cid) references courses(cid)
        on update cascade
        on delete cascade,
    
    primary key (pid)
)
-- table constraints follow
ENGINE = InnoDB;
