-- MySQL dump 10.13  Distrib 9.7.0, for Linux (x86_64)
--
-- Host: localhost    Database: medical_store
-- ------------------------------------------------------
-- Server version	9.7.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '75615ff8-56a1-11f1-a94c-6c9466159e38:1-35';

--
-- Table structure for table `cart`
--

DROP TABLE IF EXISTS `cart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cart` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `medicine_id` int DEFAULT NULL,
  `quantity` int DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`medicine_id`),
  KEY `medicine_id` (`medicine_id`),
  CONSTRAINT `cart_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `cart_ibfk_2` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cart`
--

LOCK TABLES `cart` WRITE;
/*!40000 ALTER TABLE `cart` DISABLE KEYS */;
/*!40000 ALTER TABLE `cart` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medicines`
--

DROP TABLE IF EXISTS `medicines`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicines` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `category` varchar(255) DEFAULT NULL,
  `price` float DEFAULT NULL,
  `stock` int DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `image` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1224 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicines`
--

LOCK TABLES `medicines` WRITE;
/*!40000 ALTER TABLE `medicines` DISABLE KEYS */;
INSERT INTO `medicines` VALUES (1,'Paracetamol 500 mg Tablet','Pain Relief',10,100,'2026-12-01','/static/images/paracetamol-500mg.jpg'),(2,'Paracetamol Syrup 125 mg/5ml','Pain Relief',20,69,'2026-12-01','/static/images/Paracetamol_Syrup_125_mg.jpeg'),(3,'Paracetamol Injection 150 mg/ml','Pain Relief',30,40,'2026-12-01','/static/images/Paracetamol_Injection_150_mg.jpeg'),(4,'Aspirin 75 mg Tablet','Pain Relief',10,99,'2026-11-01','default.jpg'),(5,'Ibuprofen 200 mg Tablet','Pain Relief',15,100,'2026-10-10','/static/images/WhatsApp_Image_2026-05-01_at_8.17.36_PM.jpeg'),(6,'Ibuprofen Syrup 100 mg/5ml','Pain Relief',20,80,'2026-10-10','default.jpg'),(7,'Diclofenac 50 mg Tablet','Pain Relief',15,90,'2026-09-01','default.jpg'),(8,'Diclofenac Gel 20 gm','Pain Relief',25,60,'2026-09-01','default.jpg'),(9,'Cetirizine 5 mg Tablet','Allergy',10,120,'2026-11-01','default.jpg'),(10,'Levocetirizine 5 mg Tablet','Allergy',15,100,'2026-11-01','default.jpg'),(11,'Chlorpheniramine 4 mg Tablet','Allergy',10,90,'2026-10-01','default.jpg'),(12,'Amoxicillin 500 mg Capsule','Antibiotic',50,80,'2026-09-01','default.jpg'),(13,'Amoxicillin Syrup 125 mg/5ml','Antibiotic',40,70,'2026-09-01','default.jpg'),(14,'Azithromycin 500 mg Tablet','Antibiotic',80,60,'2026-09-01','default.jpg'),(15,'Ciprofloxacin 500 mg Tablet','Antibiotic',60,75,'2026-09-01','default.jpg'),(16,'Doxycycline 100 mg Capsule','Antibiotic',55,70,'2026-09-01','default.jpg'),(17,'Fluconazole 150 mg Tablet','Antifungal',70,60,'2026-08-01','default.jpg'),(18,'Clotrimazole Cream 1%','Antifungal',45,50,'2026-08-01','default.jpg'),(19,'Metformin 500 mg Tablet','Diabetes',30,100,'2027-01-01','default.jpg'),(20,'Glimepiride 2 mg Tablet','Diabetes',40,80,'2027-01-01','default.jpg'),(21,'Amlodipine 5 mg Tablet','Cardio',20,90,'2027-01-01','default.jpg'),(22,'Telmisartan 40 mg Tablet','Cardio',50,70,'2027-01-01','default.jpg'),(23,'Atorvastatin 10 mg Tablet','Cardio',60,80,'2027-01-01','default.jpg'),(24,'Omeprazole 20 mg Capsule','Gastric',25,100,'2026-12-01','default.jpg'),(25,'Ranitidine 150 mg Tablet','Gastric',20,80,'2026-12-01','default.jpg'),(26,'ORS Powder Sachet','General',20,150,'2027-01-01','default.jpg'),(27,'Betamethasone Cream 0.05%','Dermatology',40,59,'2026-12-01','default.jpg'),(28,'Calamine Lotion','Dermatology',35,69,'2026-12-01','default.jpg'),(29,'Ciprofloxacin Eye Drops','Eye',50,49,'2026-12-01','default.jpg'),(30,'Timolol Eye Drops','Eye',60,40,'2026-12-01','default.jpg'),(31,'Hydrogen Peroxide Solution','General',30,60,'2026-12-01','default.jpg'),(32,'Ethyl Alcohol 70%','General',50,80,'2026-12-01','default.jpg'),(33,'Paracetamol 500mg','Tablet',20,100,'2026-12-31',NULL),(34,'Ibuprofen 400mg','Tablet',35,100,'2026-12-31',NULL),(35,'Amoxicillin 500mg','Capsule',120,100,'2026-12-31',NULL),(36,'Azithromycin 500mg','Tablet',150,100,'2026-12-31',NULL),(37,'Cefixime 200mg','Tablet',180,100,'2026-12-31',NULL),(38,'Ciprofloxacin 500mg','Tablet',80,100,'2026-12-31',NULL),(39,'Metformin 500mg','Tablet',30,100,'2026-12-31',NULL),(40,'Glimepiride 2mg','Tablet',45,100,'2026-12-31',NULL),(41,'Amlodipine 5mg','Tablet',35,100,'2026-12-31',NULL),(42,'Losartan 50mg','Tablet',60,100,'2026-12-31',NULL),(43,'Atorvastatin 10mg','Tablet',80,100,'2026-12-31',NULL),(44,'Rosuvastatin 10mg','Tablet',90,100,'2026-12-31',NULL),(45,'Pantoprazole 40mg','Tablet',60,100,'2026-12-31',NULL),(46,'Omeprazole 20mg','Capsule',50,100,'2026-12-31',NULL),(47,'Rabeprazole 20mg','Tablet',65,100,'2026-12-31',NULL),(48,'Domperidone 10mg','Tablet',40,100,'2026-12-31',NULL),(49,'Ondansetron 4mg','Tablet',55,100,'2026-12-31',NULL),(50,'Cetirizine 10mg','Tablet',25,100,'2026-12-31',NULL),(51,'Levocetirizine 5mg','Tablet',30,100,'2026-12-31',NULL),(52,'Montelukast 10mg','Tablet',90,100,'2026-12-31',NULL),(53,'Dextromethorphan Syrup','Syrup',70,100,'2026-12-31',NULL),(54,'Ambroxol Syrup','Syrup',60,100,'2026-12-31',NULL),(55,'Salbutamol Inhaler','Inhaler',180,100,'2026-12-31',NULL),(56,'Beclomethasone Inhaler','Inhaler',250,100,'2026-12-31',NULL),(57,'Diclofenac 50mg','Tablet',30,100,'2026-12-31',NULL),(58,'Paracetamol 650mg','Tablet',25,100,'2026-12-31',NULL),(59,'Aspirin 75mg','Tablet',25,100,'2026-12-31',NULL),(60,'Clopidogrel 75mg','Tablet',120,100,'2026-12-31',NULL),(61,'Warfarin 5mg','Tablet',60,100,'2026-12-31',NULL),(62,'Heparin Injection','Injection',200,100,'2026-12-31',NULL),(63,'Tranexamic Acid 500mg','Tablet',90,100,'2026-12-31',NULL),(64,'Vitamin C 500mg','Tablet',35,100,'2026-12-31',NULL),(65,'Vitamin B Complex','Tablet',40,100,'2026-12-31',NULL),(66,'Iron Folic Acid','Tablet',45,100,'2026-12-31',NULL),(67,'Zinc Tablets','Tablet',30,100,'2026-12-31',NULL),(68,'ORS Powder','Sachet',20,100,'2026-12-31',NULL),(69,'Loperamide 2mg','Tablet',25,100,'2026-12-31',NULL),(70,'Dicyclomine 20mg','Tablet',40,100,'2026-12-31',NULL),(71,'Ranitidine 150mg','Tablet',30,100,'2026-12-31',NULL),(72,'Sucralfate Syrup','Syrup',90,100,'2026-12-31',NULL),(73,'Multivitamin Tablets','Tablet',60,100,'2026-12-31',NULL),(74,'Calcium + Vitamin D3','Tablet',55,100,'2026-12-31',NULL),(75,'Cough Syrup','Syrup',70,100,'2026-12-31',NULL),(76,'Betadine Solution','Antiseptic',50,100,'2026-12-31',NULL),(77,'Dettol Solution','Antiseptic',60,100,'2026-12-31',NULL),(78,'Hydrogen Peroxide','Antiseptic',25,100,'2026-12-31',NULL),(79,'Povidone Iodine Ointment','Ointment',80,100,'2026-12-31',NULL),(80,'Neosporin Ointment','Ointment',90,100,'2026-12-31',NULL),(81,'Clotrimazole Cream','Cream',75,100,'2026-12-31',NULL),(82,'Ketoconazole Shampoo','Shampoo',180,100,'2026-12-31',NULL),(83,'Minoxidil Solution','Hair Care',300,100,'2026-12-31',NULL),(84,'Finasteride 1mg','Tablet',250,100,'2026-12-31',NULL),(85,'Albendazole 400mg','Tablet',30,100,'2026-12-31',NULL),(86,'Mebendazole 100mg','Tablet',25,100,'2026-12-31',NULL),(87,'Ivermectin 12mg','Tablet',60,100,'2026-12-31',NULL),(88,'Doxycycline 100mg','Tablet',70,100,'2026-12-31',NULL),(89,'Linezolid 600mg','Tablet',400,100,'2026-12-31',NULL),(90,'Vancomycin Injection','Injection',900,100,'2026-12-31',NULL),(91,'Meropenem Injection','Injection',800,100,'2026-12-31',NULL),(92,'Piperacillin Tazobactam','Injection',650,100,'2026-12-31',NULL),(93,'Levofloxacin 500mg','Tablet',90,100,'2026-12-31',NULL),(94,'Norfloxacin 400mg','Tablet',60,100,'2026-12-31',NULL),(95,'Chlorpheniramine 4mg','Tablet',20,100,'2026-12-31',NULL),(96,'Diphenhydramine Syrup','Syrup',50,100,'2026-12-31',NULL),(97,'Guaifenesin Syrup','Syrup',65,100,'2026-12-31',NULL),(98,'Activated Charcoal','Tablet',35,100,'2026-12-31',NULL),(99,'Bisacodyl 5mg','Tablet',30,100,'2026-12-31',NULL),(100,'Senna Tablets','Tablet',25,100,'2026-12-31',NULL),(101,'Furosemide 40mg','Tablet',40,100,'2026-12-31',NULL),(102,'Spironolactone 25mg','Tablet',45,100,'2026-12-31',NULL),(103,'Digoxin 0.25mg','Tablet',60,100,'2026-12-31',NULL),(104,'Sitagliptin 50mg','Tablet',400,100,'2026-12-31',NULL),(105,'Vildagliptin 50mg','Tablet',380,100,'2026-12-31',NULL),(106,'Dapagliflozin 10mg','Tablet',450,100,'2026-12-31',NULL),(107,'Empagliflozin 10mg','Tablet',480,100,'2026-12-31',NULL),(108,'Pioglitazone 15mg','Tablet',120,100,'2026-12-31',NULL),(109,'Glipizide 5mg','Tablet',60,100,'2026-12-31',NULL),(110,'Sertraline 50mg','Tablet',180,100,'2026-12-31',NULL),(111,'Fluoxetine 20mg','Tablet',160,100,'2026-12-31',NULL),(112,'Escitalopram 10mg','Tablet',170,100,'2026-12-31',NULL),(113,'Venlafaxine 75mg','Tablet',220,100,'2026-12-31',NULL),(114,'Duloxetine 30mg','Tablet',240,100,'2026-12-31',NULL),(115,'Amitriptyline 25mg','Tablet',90,100,'2026-12-31',NULL),(116,'Olanzapine 5mg','Tablet',300,100,'2026-12-31',NULL),(117,'Risperidone 2mg','Tablet',250,100,'2026-12-31',NULL),(118,'Quetiapine 100mg','Tablet',280,100,'2026-12-31',NULL),(119,'Aripiprazole 10mg','Tablet',350,100,'2026-12-31',NULL),(120,'Levothyroxine 50mcg','Tablet',60,100,'2026-12-31',NULL),(121,'Carbimazole 10mg','Tablet',70,100,'2026-12-31',NULL),(122,'Amiodarone 200mg','Tablet',150,100,'2026-12-31',NULL),(123,'Propranolol 40mg','Tablet',90,100,'2026-12-31',NULL),(124,'Atenolol 50mg','Tablet',80,100,'2026-12-31',NULL),(125,'Tamsulosin 0.4mg','Tablet',150,100,'2026-12-31',NULL),(126,'Sildenafil 50mg','Tablet',180,100,'2026-12-31',NULL),(127,'Tadalafil 10mg','Tablet',200,100,'2026-12-31',NULL),(128,'Dutasteride 0.5mg','Tablet',250,100,'2026-12-31',NULL),(129,'Hydroxychloroquine 200mg','Tablet',150,100,'2026-12-31',NULL),(130,'Artemether Lumefantrine','Tablet',180,100,'2026-12-31',NULL),(131,'Atovaquone Proguanil','Tablet',500,100,'2026-12-31',NULL),(132,'Roxithromycin 150mg','Tablet',120,100,'2026-12-31',NULL),(133,'Clarithromycin 500mg','Tablet',160,100,'2026-12-31',NULL),(134,'Erythromycin 250mg','Tablet',90,100,'2026-12-31',NULL),(135,'Tetracycline 500mg','Tablet',80,100,'2026-12-31',NULL),(136,'Minocycline 100mg','Tablet',110,100,'2026-12-31',NULL),(137,'Gentamicin Injection','Injection',150,100,'2026-12-31',NULL),(138,'Tobramycin Injection','Injection',180,100,'2026-12-31',NULL),(139,'Amikacin Injection','Injection',200,100,'2026-12-31',NULL),(140,'Streptomycin Injection','Injection',140,100,'2026-12-31',NULL),(141,'Ceftriaxone 1g','Injection',250,100,'2026-12-31',NULL),(142,'Cefotaxime 1g','Injection',220,100,'2026-12-31',NULL),(143,'Cefuroxime 500mg','Tablet',180,100,'2026-12-31',NULL),(144,'Cefpodoxime 200mg','Tablet',170,100,'2026-12-31',NULL),(145,'Cefadroxil 500mg','Tablet',150,100,'2026-12-31',NULL),(146,'Cloxacillin 500mg','Tablet',130,100,'2026-12-31',NULL),(147,'Dicloxacillin 500mg','Tablet',140,100,'2026-12-31',NULL),(148,'Penicillin V 250mg','Tablet',80,100,'2026-12-31',NULL),(149,'Ampicillin 500mg','Capsule',90,100,'2026-12-31',NULL),(150,'Sulbactam Injection','Injection',300,100,'2026-12-31',NULL),(151,'Amoxiclav 625mg','Tablet',180,100,'2026-12-31',NULL),(152,'Co-trimoxazole','Tablet',70,100,'2026-12-31',NULL),(153,'Trimethoprim 160mg','Tablet',60,100,'2026-12-31',NULL),(154,'Nitrofurantoin 100mg','Tablet',90,100,'2026-12-31',NULL),(155,'Fosfomycin Sachet','Sachet',200,100,'2026-12-31',NULL),(156,'Linezolid 300mg','Tablet',320,100,'2026-12-31',NULL),(157,'Daptomycin Injection','Injection',900,100,'2026-12-31',NULL),(158,'Colistin Injection','Injection',850,100,'2026-12-31',NULL),(159,'Teicoplanin Injection','Injection',780,100,'2026-12-31',NULL),(160,'Clindamycin 150mg','Tablet',110,100,'2026-12-31',NULL),(161,'Metronidazole 200mg','Tablet',50,100,'2026-12-31',NULL),(162,'Tinidazole 500mg','Tablet',80,100,'2026-12-31',NULL),(163,'Secnidazole 1g','Tablet',120,100,'2026-12-31',NULL),(164,'Albendazole Chewable','Tablet',35,100,'2026-12-31',NULL),(165,'Praziquantel 600mg','Tablet',200,100,'2026-12-31',NULL),(166,'Mebendazole Suspension','Syrup',40,100,'2024-01-31',NULL),(167,'Artemisinin Combination','Tablet',180,100,'2026-12-31',NULL),(168,'Quinine Sulphate','Tablet',150,100,'2026-12-31',NULL),(169,'Primaquine 15mg','Tablet',90,100,'2026-12-31',NULL),(170,'Chloroquine Phosphate','Tablet',100,100,'2026-12-31',NULL),(171,'Atovaquone 250mg','Tablet',450,100,'2026-12-31',NULL),(172,'Proguanil 100mg','Tablet',300,100,'2026-12-31',NULL),(173,'Oseltamivir 75mg','Capsule',500,100,'2026-12-31',NULL),(174,'Zanamivir Inhaler','Inhaler',650,100,'2026-12-31',NULL),(175,'Remdesivir Injection','Injection',1200,100,'2026-12-31',NULL),(176,'Favipiravir 200mg','Tablet',600,100,'2026-12-31',NULL),(177,'Molnupiravir 200mg','Tablet',700,100,'2026-12-31',NULL),(178,'Acyclovir 400mg','Tablet',150,100,'2026-12-31',NULL),(179,'Valacyclovir 500mg','Tablet',300,100,'2026-12-31',NULL),(180,'Ganciclovir Injection','Injection',900,100,'2026-12-31',NULL),(181,'Famciclovir 250mg','Tablet',280,100,'2026-12-31',NULL),(182,'Tenofovir Alafenamide','Tablet',500,100,'2026-12-31',NULL),(183,'Ribavirin 200mg','Tablet',350,100,'2026-12-31',NULL),(184,'Interferon Alfa Injection','Injection',1500,100,'2026-12-31',NULL),(185,'Etanercept Injection','Injection',2000,100,'2026-12-31',NULL),(186,'Adalimumab Injection','Injection',2500,100,'2026-12-31',NULL),(187,'Infliximab Injection','Injection',3000,100,'2026-12-31',NULL),(188,'Rituximab Injection','Injection',3500,100,'2026-12-31',NULL),(189,'Bevacizumab Injection','Injection',4000,100,'2026-12-31',NULL),(190,'Trastuzumab Injection','Injection',4500,100,'2026-12-31',NULL),(191,'Epoetin Alfa Injection','Injection',800,100,'2026-12-31',NULL),(192,'Darbepoetin Alfa','Injection',900,100,'2026-12-31',NULL),(193,'Filgrastim Injection','Injection',700,100,'2026-12-31',NULL),(194,'Pegfilgrastim Injection','Injection',1200,100,'2026-12-31',NULL),(195,'Insulin Glargine','Injection',400,100,'2026-12-31',NULL),(196,'Insulin Lispro','Injection',380,100,'2026-12-31',NULL),(197,'Insulin Aspart','Injection',370,100,'2026-12-31',NULL),(198,'Human Insulin','Injection',350,100,'2026-12-31',NULL),(199,'Glucagon Injection','Injection',500,100,'2026-12-31',NULL),(200,'Dexamethasone 4mg','Tablet',60,100,'2026-12-31',NULL),(201,'Prednisone 20mg','Tablet',80,100,'2026-12-31',NULL),(202,'Methylprednisolone 16mg','Tablet',120,100,'2026-12-31',NULL),(203,'Betamethasone Injection','Injection',150,100,'2026-12-31',NULL),(204,'Fluticasone Nasal Spray','Spray',200,100,'2026-12-31',NULL),(205,'Budesonide Inhaler','Inhaler',250,100,'2026-12-31',NULL),(206,'Formoterol Inhaler','Inhaler',300,100,'2026-12-31',NULL),(207,'Salmeterol Inhaler','Inhaler',320,100,'2026-12-31',NULL),(208,'Ipratropium Inhaler','Inhaler',280,100,'2026-12-31',NULL),(209,'Theophylline 200mg','Tablet',90,100,'2026-12-31',NULL),(210,'Montelukast 5mg','Tablet',80,100,'2026-12-31',NULL),(211,'Zafirlukast 20mg','Tablet',100,100,'2026-12-31',NULL),(212,'Azelastine Nasal Spray','Spray',150,100,'2026-12-31',NULL),(213,'Olopatadine Eye Drops','Eye Drops',120,100,'2026-12-31',NULL),(214,'Ketotifen Eye Drops','Eye Drops',90,100,'2026-12-31',NULL),(215,'Brinzolamide Eye Drops','Eye Drops',180,100,'2026-12-31',NULL),(216,'Acetaminophen Injection','Injection',100,100,'2026-12-31',NULL),(217,'Ketorolac Injection','Injection',120,100,'2026-12-31',NULL),(218,'Tramadol Injection','Injection',150,100,'2026-12-31',NULL),(219,'Morphine Injection','Injection',300,100,'2026-12-31',NULL),(220,'Fentanyl Patch','Patch',500,100,'2026-12-31',NULL),(221,'Lidocaine Injection','Injection',80,100,'2026-12-31',NULL),(222,'Bupivacaine Injection','Injection',90,100,'2026-12-31',NULL),(223,'Ropivacaine Injection','Injection',110,100,'2026-12-31',NULL),(224,'Nalbuphine Injection','Injection',150,100,'2026-12-31',NULL),(225,'Diclofenac Gel','Gel',70,100,'2026-12-31',NULL),(226,'Ketoprofen Gel','Gel',80,100,'2026-12-31',NULL),(227,'Mupirocin Ointment','Ointment',120,100,'2026-12-31',NULL),(228,'Silver Sulfadiazine Cream','Cream',150,100,'2026-12-31',NULL),(229,'Hydrocortisone Cream','Cream',65,100,'2026-12-31',NULL),(230,'Clobetasol Cream','Cream',90,100,'2026-12-31',NULL),(231,'Tacrolimus Ointment','Ointment',200,100,'2026-12-31',NULL),(232,'Pimecrolimus Cream','Cream',180,100,'2026-12-31',NULL),(233,'Terbinafine Cream','Cream',140,100,'2026-12-31',NULL),(234,'Luliconazole Cream','Cream',160,100,'2026-12-31',NULL),(235,'Sertaconazole Cream','Cream',150,100,'2026-12-31',NULL),(236,'Sodium Chloride Injection','Injection',50,100,'2026-12-31',NULL),(237,'Dextrose 5% IV','IV Fluid',60,100,'2026-12-31',NULL),(238,'Ringer Lactate','IV Fluid',70,100,'2026-12-31',NULL),(239,'Normal Saline','IV Fluid',50,100,'2026-12-31',NULL),(240,'Potassium Chloride','Injection',80,100,'2026-12-31',NULL),(241,'Magnesium Sulphate','Injection',90,100,'2026-12-31',NULL),(242,'Calcium Gluconate','Injection',100,100,'2026-12-31',NULL),(243,'Sodium Bicarbonate Injection','Injection',70,100,'2026-12-31',NULL),(244,'Heparin Low Molecular Weight','Injection',300,100,'2026-12-31',NULL),(245,'Enoxaparin Injection','Injection',350,100,'2026-12-31',NULL),(246,'Gliclazide 80mg','Diabetes',50,100,'2026-12-31',NULL),(247,'Ofloxacin 200mg','Antibiotic',70,100,'2026-12-31',NULL),(248,'Clindamycin 300mg','Antibiotic',120,100,'2026-12-31',NULL),(249,'Metronidazole 400mg','Antibiotic',45,100,'2026-12-31',NULL),(250,'Rifampicin 450mg','Anti-TB',120,100,'2026-12-31',NULL),(251,'Isoniazid 300mg','Anti-TB',60,100,'2026-12-31',NULL),(252,'Ethambutol 800mg','Anti-TB',70,100,'2026-12-31',NULL),(253,'Pyrazinamide 500mg','Anti-TB',80,100,'2026-12-31',NULL),(254,'Tenofovir 300mg','Antiviral',350,100,'2026-12-31',NULL),(255,'Lamivudine 300mg','Antiviral',200,100,'2026-12-31',NULL),(256,'Zidovudine 300mg','Antiviral',300,100,'2026-12-31',NULL),(257,'Efavirenz 600mg','Antiviral',450,100,'2026-12-31',NULL),(258,'Dolutegravir 50mg','Antiviral',600,100,'2026-12-31',NULL),(259,'Fluconazole 150mg','Antifungal',90,100,'2026-12-31',NULL),(260,'Itraconazole 100mg','Antifungal',180,100,'2026-12-31',NULL),(261,'Terbinafine 250mg','Antifungal',150,100,'2026-12-31',NULL),(262,'Griseofulvin 500mg','Antifungal',200,100,'2026-12-31',NULL),(263,'Prednisolone 10mg','Steroid',90,100,'2026-12-31',NULL),(264,'Hydrocortisone','Steroid',65,100,'2026-12-31',NULL),(265,'Fexofenadine 120mg','Antihistamine',90,100,'2026-12-31',NULL),(266,'Sucralfate','GI',90,100,'2026-12-31',NULL),(267,'Calcium + D3','Supplement',55,100,'2026-12-31',NULL),(268,'Chloroquine 250mg','Antimalarial',100,100,'2026-12-31',NULL),(269,'Remdesivir','Injection',1200,100,'2026-12-31',NULL),(270,'Meropenem 1g','Injection',800,100,'2026-12-31',NULL),(271,'Vancomycin','Injection',900,100,'2026-12-31',NULL),(272,'Gentamicin','Injection',150,100,'2026-12-31',NULL),(273,'Amikacin','Injection',200,100,'2026-12-31',NULL),(274,'Heparin','Injection',200,100,'2026-12-31',NULL),(275,'Enoxaparin','Injection',350,100,'2026-12-31',NULL),(276,'Mupirocin','Ointment',120,100,'2026-12-31',NULL),(277,'Ketoconazole Cream','Cream',90,100,'2026-12-31',NULL),(278,'Silver Sulfadiazine','Cream',150,100,'2026-12-31',NULL),(279,'Minoxidil','Topical',300,100,'2026-12-31',NULL),(280,'Dutasteride','Urology',250,100,'2026-12-31',NULL),(281,'Tamsulosin','Urology',150,100,'2026-12-31',NULL),(282,'Sildenafil','Urology',180,100,'2026-12-31',NULL),(283,'Tadalafil','Urology',200,100,'2026-12-31',NULL),(284,'Acetaminophen 650mg','Analgesic',25,100,'2026-12-31',NULL),(285,'Naproxen 250mg','Analgesic',40,100,'2026-12-31',NULL),(286,'Etodolac 300mg','Analgesic',55,100,'2026-12-31',NULL),(287,'Ketorolac 10mg','Analgesic',60,100,'2026-12-31',NULL),(288,'Meloxicam 7.5mg','Analgesic',70,100,'2026-12-31',NULL),(289,'Piroxicam 20mg','Analgesic',65,100,'2026-12-31',NULL),(290,'Celecoxib 200mg','Analgesic',120,100,'2026-12-31',NULL),(291,'Etoricoxib 90mg','Analgesic',140,100,'2026-12-31',NULL),(292,'Indomethacin 25mg','Analgesic',50,100,'2026-12-31',NULL),(293,'Aceclofenac 100mg','Analgesic',45,100,'2026-12-31',NULL),(294,'Lactulose Syrup','GI',120,100,'2026-12-31',NULL),(295,'Pantoprazole 20mg','Gastric',55,100,'2026-12-31',NULL),(296,'Esomeprazole 40mg','Gastric',80,100,'2026-12-31',NULL),(297,'Dexlansoprazole 30mg','Gastric',100,100,'2025-12-15',NULL),(298,'Cimetidine 200mg','GI',35,100,'2026-12-31',NULL),(299,'Famotidine 20mg','GI',40,100,'2026-12-31',NULL),(300,'Rifaximin 200mg','Antibiotic',200,100,'2026-12-31',NULL),(301,'Spiramycin 3M IU','Antibiotic',250,100,'2026-12-31',NULL),(302,'Cefaclor 250mg','Antibiotic',120,100,'2026-12-31',NULL),(303,'Cefuroxime Axetil 500mg','Antibiotic',180,100,'2026-12-31',NULL),(304,'Piperacillin + Tazobactam','Antibiotic',500,100,'2026-12-31',NULL),(305,'Imipenem 500mg','Antibiotic',700,100,'2026-12-31',NULL),(306,'Ertapenem 1g','Antibiotic',800,100,'2026-12-31',NULL),(307,'Doripenem 500mg','Antibiotic',850,100,'2026-12-31',NULL),(308,'Tigecycline 50mg','Antibiotic',900,100,'2026-12-31',NULL),(309,'Polymyxin B','Antibiotic',950,100,'2026-12-31',NULL),(310,'Bacitracin Ointment','Antibiotic',60,100,'2026-12-31',NULL),(311,'Neomycin Cream','Antibiotic',55,100,'2026-12-31',NULL),(312,'Ofloxacin Eye Drops','Eye Drops',70,100,'2026-12-31',NULL),(313,'Moxifloxacin Eye Drops','Eye Drops',120,100,'2026-12-31',NULL),(314,'Tobramycin Eye Drops','Eye Drops',100,100,'2026-12-31',NULL),(315,'Atropine Eye Drops','Eye Drops',90,100,'2026-12-31',NULL),(316,'Cyclopentolate Eye Drops','Eye Drops',110,100,'2026-12-31',NULL),(317,'Brimonidine Eye Drops','Eye Drops',200,100,'2026-12-31',NULL),(318,'Latanoprost Eye Drops','Eye Drops',300,100,'2026-12-31',NULL),(319,'Travoprost Eye Drops','Eye Drops',320,100,'2026-12-31',NULL),(320,'Dorzolamide Eye Drops','Eye Drops',180,100,'2026-12-31',NULL),(321,'Brinzolamide + Timolol','Eye Drops',250,100,'2026-12-31',NULL),(322,'Betaxolol Eye Drops','Eye Drops',160,100,'2026-12-31',NULL),(323,'Ketorolac Eye Drops','Eye Drops',90,100,'2026-12-31',NULL),(324,'Quetiapine 50mg','Psychiatric',150,100,'2026-12-31',NULL),(325,'Clozapine 25mg','Psychiatric',180,100,'2026-12-31',NULL),(326,'Paroxetine 20mg','Psychiatric',130,100,'2026-12-31',NULL),(327,'Nortriptyline 10mg','Psychiatric',90,100,'2026-12-31',NULL),(328,'Diazepam 5mg','Psychiatric',60,100,'2026-12-31',NULL),(329,'Clonazepam 0.5mg','Psychiatric',70,100,'2026-12-31',NULL),(330,'Lorazepam 1mg','Psychiatric',65,100,'2026-12-31',NULL),(331,'Alprazolam 0.5mg','Psychiatric',80,100,'2026-12-31',NULL),(332,'Zolpidem 10mg','Sleep',90,100,'2026-12-31',NULL),(333,'Zopiclone 7.5mg','Sleep',85,100,'2026-12-31',NULL),(334,'Melatonin 3mg','Sleep',60,100,'2026-12-31',NULL),(335,'Hydroxyzine 25mg','Antihistamine',70,100,'2026-12-31',NULL),(336,'Diphenhydramine 25mg','Antihistamine',30,100,'2026-12-31',NULL),(337,'Rupatadine 10mg','Antihistamine',90,100,'2026-12-31',NULL),(338,'Desloratadine 5mg','Antihistamine',80,100,'2026-12-31',NULL),(339,'Cough Syrup Dextromethorphan','Cough',60,100,'2026-12-31',NULL),(340,'Ambroxol 30mg','Cough',55,100,'2026-12-31',NULL),(341,'Bromhexine 8mg','Cough',50,100,'2026-12-31',NULL),(342,'Guaifenesin 100mg','Cough',45,100,'2026-12-31',NULL),(343,'Levosalbutamol Syrup','Respiratory',70,100,'2026-12-31',NULL),(344,'Budesonide Respules','Inhaler',180,100,'2026-12-31',NULL),(345,'Ipratropium Bromide','Inhaler',150,100,'2026-12-31',NULL),(346,'Tiotropium Inhaler','Inhaler',300,100,'2026-12-31',NULL),(347,'Fluticasone Inhaler','Inhaler',280,100,'2026-12-31',NULL),(348,'Montelukast + Levocetirizine','Respiratory',100,100,'2026-12-31',NULL),(349,'ORS Electrolyte Powder','Supplement',20,100,'2026-12-31',NULL),(350,'Biotin Tablets','Supplement',60,100,'2026-12-31',NULL),(351,'Vitamin D3 60000 IU','Supplement',90,100,'2026-12-31',NULL),(352,'Omega 3 Capsules','Supplement',120,100,'2026-12-31',NULL),(353,'Coenzyme Q10','Supplement',250,100,'2026-12-31',NULL),(354,'Glucosamine Sulphate','Supplement',180,100,'2026-12-31',NULL),(355,'Chondroitin Sulphate','Supplement',200,100,'2026-12-31',NULL),(356,'Lycopene Capsules','Supplement',150,100,'2026-12-31',NULL),(357,'Silymarin 140mg','Liver',120,100,'2026-12-31',NULL),(358,'Ursodeoxycholic Acid','Liver',180,100,'2026-12-31',NULL),(359,'Domperidone + Pantoprazole','Gastric',90,100,'2026-12-31',NULL),(360,'Ondansetron Oral Film','Gastric',70,100,'2026-12-31',NULL),(361,'Lansoprazole 30mg','Gastric',85,100,'2026-12-31',NULL),(362,'Magaldrate Syrup','Gastric',60,100,'2026-12-31',NULL),(363,'Sucralfate Suspension','Gastric',95,100,'2026-12-31',NULL),(364,'ORS Zinc Combination','Supplement',35,100,'2026-12-31',NULL),(365,'Permethrin Cream','Skin',90,100,'2026-12-31',NULL),(366,'Clindamycin Gel','Skin',80,100,'2026-12-31',NULL),(367,'Adapalene Gel','Skin',150,100,'2026-05-07',NULL),(368,'Tretinoin Cream','Skin',200,100,'2026-12-31',NULL),(369,'Benzoyl Peroxide','Skin',120,100,'2026-12-31',NULL),(370,'Hydroquinone Cream','Skin',180,100,'2026-12-31',NULL),(1217,'Paracetamol 650','Tablet',35,0,'2026-01-28',NULL),(1218,'Crocin Advance','Tablet',25,0,'2026-05-30',NULL),(1219,'paracetamol 650','medicine',35,12,'2026-05-07',NULL),(1220,'Unknown Medicine','General',0,10,NULL,'/static/uploads/1778490085.240985.jpg'),(1221,'Unknown Medicine','General',0,10,NULL,'/static/uploads/1778490154.777258.jpg'),(1222,'Unknown Medicine','General',0,10,NULL,'/static/uploads/1778490323.853751.jpg'),(1223,'Unknown Medicine','General',0,10,NULL,'/static/uploads/1778490348.312042.jpg');
/*!40000 ALTER TABLE `medicines` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_items`
--

DROP TABLE IF EXISTS `order_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int DEFAULT NULL,
  `medicine_id` int DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `price` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `order_id` (`order_id`),
  KEY `medicine_id` (`medicine_id`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_items`
--

LOCK TABLES `order_items` WRITE;
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
INSERT INTO `order_items` VALUES (1,1,2,4,20);
/*!40000 ALTER TABLE `order_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `total` float DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `status` varchar(100) DEFAULT NULL,
  `prescription` text,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (1,3,80,'2026-05-25 13:58:35','Delivered',NULL);
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff`
--

DROP TABLE IF EXISTS `staff`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `contact` varchar(50) DEFAULT NULL,
  `age` int DEFAULT NULL,
  `gender` varchar(50) DEFAULT NULL,
  `religion` varchar(100) DEFAULT NULL,
  `address` text,
  `education` varchar(255) DEFAULT NULL,
  `aadhar` varchar(50) DEFAULT NULL,
  `pan` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff`
--

LOCK TABLES `staff` WRITE;
/*!40000 ALTER TABLE `staff` DISABLE KEYS */;
INSERT INTO `staff` VALUES (1,'Sujal ','katkarsujal3@gmail.com','7498513789',21,'Male','Hindu','virar west , yashwant nagar, sky City housing society, H-1205','TYBSCIT ','68678889','Panid');
/*!40000 ALTER TABLE `staff` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `address` text,
  `role` varchar(50) DEFAULT NULL,
  `password` text,
  `hashed_password` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Admin','admin@gmail.com','9999999999','Virar','owner','admin123','scrypt:32768:8:1$tWGGKrfzcPbwjHof$5b009e7b66a6e87d7ba79e9bce4312dc241fb380e8c65c855bf848e36643c6b99c580316d58b1091f7ca364826326b0c44b3be95b6b48246fdb6906b43a169ca'),(2,'Staff','staff@gmail.com','7498513789','Virar','staff','staff123','scrypt:32768:8:1$nQmtMKpc3PeFUHYl$3c4cca15e80077063af6823a828b9b7342fa89440d1af10a237e2a1b117437116c24e720f1146bef184e4cf8b5bab7d95a66248297a7ed4954c8428094ebba36'),(3,'Customer','customer@gmail.com','7498513789','Virar','customer','customer123','scrypt:32768:8:1$8RNv4oBOTDU6XtXQ$4f485dda9ddbf688f41e8185524d7ab717e3fff72f7d0225d1f6c2e9d1f57f88b147decd44f561b1b5c6bd4dbbcc675a0435d0e58332b0f2c43e048f91ba2833'),(4,'Sujal ','katkarsujal3@gmail.com','7498513789','virar west , yashwant nagar, sky City housing society, H-1205','staff',NULL,'scrypt:32768:8:1$4aOmxO55eOiDxf0n$b978a4d4f9bbd5ff04e141ddcc13159fc0c996ab2b7d969536c7ff4bd58345f3a5cbab256a022ea0bdeaa838eee0977e184b486533d262883f0f57596ed63917');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-25 16:16:30
