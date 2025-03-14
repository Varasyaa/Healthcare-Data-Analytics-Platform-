-- Create a new database (from psql, you might run: CREATE DATABASE healthcare_db;)

-- Table for patients
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table for doctors
CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    specialization VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table for patient visits
CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER REFERENCES doctors(id) ON DELETE SET NULL,
    visit_date TIMESTAMP DEFAULT NOW(),
    diagnosis TEXT,
    treatment TEXT
);

-- Table for lab results
CREATE TABLE lab_results (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    test_type VARCHAR(100),
    test_date DATE,
    result_value NUMERIC(10, 2),
    units VARCHAR(20),
    reference_range VARCHAR(50)
);
