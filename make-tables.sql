use c9;

drop table if exists users;  -- allows us to source the batch file more than once
drop table if exists courses;  -- allows us to source the batch file more than once
drop table if exists posts;  -- allows us to source the batch file more than once

CREATE TABLE users (
    name varchar(30),
    uid int auto_increment,
    hashedPW char(60), -- what is the space we should alot here?
    isAdmin enum('0', '1'),
    primary key (uid)
)

-- table constraints follow
ENGINE = InnoDB;

CREATE TABLE courses (
    name varchar(30),
    cid int auto_increment,
    semester char(3), -- ie F19, S19
    primary key (cid)
)
-- table constraints follow
ENGINE = InnoDB;

CREATE TABLE posts (
    pid int auto_increment,
    rating enum('1', '2', '3', '4', '5'),
    uid int not null,
    primary key (pid),
    
    INDEX (uid),     -- necessary for referential integrity checking
    foreign key (uid) references users(uid)
        on update cascade
        on delete cascade
)
-- table constraints follow
ENGINE = InnoDB;
