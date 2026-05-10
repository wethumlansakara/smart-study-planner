-- Smart Study Planner — MySQL schema
-- Run this once to set up the database.

CREATE DATABASE IF NOT EXISTS smart_study_planner
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE smart_study_planner;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100)  NOT NULL,
    email     VARCHAR(150)  NOT NULL UNIQUE,
    phone     VARCHAR(20),
    password  VARCHAR(255)  NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    subject_name  VARCHAR(150) NOT NULL,
    difficulty    ENUM('low','medium','high') NOT NULL DEFAULT 'medium',
    hours         INT NOT NULL DEFAULT 0,
    weekly_hours  INT NOT NULL DEFAULT 0,
    exam_date     DATE,
    progress      INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
