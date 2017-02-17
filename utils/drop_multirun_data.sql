/*
 *  This script is meant to wipe the Oracle database out of the multirun data. *
 *  It simply drops all the tables along with the data.                        *
 *  To use it go to the directory where it is located, log into the            *
 *  database shell (using sqlplus) and type "@drop_multirun_data.sql"          *
/*

DROP TABLE dataset           CASCADE CONSTRAINTS PURGE;
DROP TABLE eos_dir           CASCADE CONSTRAINTS PURGE;
DROP TABLE filename          CASCADE CONSTRAINTS PURGE;
DROP TABLE multirun          CASCADE CONSTRAINTS PURGE;
DROP TABLE multirun_state    CASCADE CONSTRAINTS PURGE;
DROP TABLE run_dataset       CASCADE CONSTRAINTS PURGE;
DROP TABLE run_info          CASCADE CONSTRAINTS PURGE;
DROP TABLE run_multirun      CASCADE CONSTRAINTS PURGE;
DROP TABLE processing_time   CASCADE CONSTRAINTS PURGE;
DROP TABLE jenkins_job_type  CASCADE CONSTRAINTS PURGE;
DROP TABLE jenkins_build_url CASCADE CONSTRAINTS PURGE;
