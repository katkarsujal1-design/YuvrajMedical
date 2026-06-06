-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: medical_store
-- ------------------------------------------------------
-- Server version	8.0.46

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
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `barcode` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1225 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicines`
--

LOCK TABLES `medicines` WRITE;
/*!40000 ALTER TABLE `medicines` DISABLE KEYS */;
INSERT INTO `medicines` VALUES (1,'Paracetamol 500 mg Tablet','Pain Relief',10,100,'2026-12-01','/static/images/paracetamol-500mg.jpg','YM000001'),(2,'Paracetamol Syrup 125 mg/5ml','Pain Relief',20,65,'2026-12-01','/static/images/Paracetamol_Syrup_125_mg.jpeg','YM000002'),(3,'Paracetamol Injection 150 mg/ml','Pain Relief',30,37,'2026-12-01','/static/images/Paracetamol_Injection_150_mg.jpeg','YM000003'),(4,'Aspirin 75 mg Tablet','Pain Relief',10,97,'2026-11-01','default.jpg','YM000004'),(5,'Ibuprofen 200 mg Tablet','Pain Relief',15,100,'2026-10-10','/static/images/WhatsApp_Image_2026-05-01_at_8.17.36_PM.jpeg','YM000005'),(6,'Ibuprofen Syrup 100 mg/5ml','Pain Relief',20,80,'2026-10-10','default.jpg','YM000006'),(7,'Diclofenac 50 mg Tablet','Pain Relief',15,90,'2026-09-01','default.jpg','YM000007'),(8,'Diclofenac Gel 20 gm','Pain Relief',25,60,'2026-09-01','default.jpg','YM000008'),(9,'Cetirizine 5 mg Tablet','Allergy',10,120,'2026-11-01','default.jpg','YM000009'),(10,'Levocetirizine 5 mg Tablet','Allergy',15,100,'2026-11-01','default.jpg','YM000010'),(11,'Chlorpheniramine 4 mg Tablet','Allergy',10,90,'2026-10-01','default.jpg','YM000011'),(12,'Amoxicillin 500 mg Capsule','Antibiotic',50,80,'2026-09-01','default.jpg','YM000012'),(13,'Amoxicillin Syrup 125 mg/5ml','Antibiotic',40,69,'2026-09-01','default.jpg','YM000013'),(14,'Azithromycin 500 mg Tablet','Antibiotic',80,60,'2026-09-01','default.jpg','YM000014'),(15,'Ciprofloxacin 500 mg Tablet','Antibiotic',60,75,'2026-09-01','default.jpg','YM000015'),(16,'Doxycycline 100 mg Capsule','Antibiotic',55,70,'2026-09-01','default.jpg','YM000016'),(17,'Fluconazole 150 mg Tablet','Antifungal',70,60,'2026-08-01','default.jpg','YM000017'),(18,'Clotrimazole Cream 1%','Antifungal',45,50,'2026-08-01','default.jpg','YM000018'),(19,'Metformin 500 mg Tablet','Diabetes',30,100,'2027-01-01','default.jpg','YM000019'),(20,'Glimepiride 2 mg Tablet','Diabetes',40,80,'2027-01-01','default.jpg','YM000020'),(21,'Amlodipine 5 mg Tablet','Cardio',20,90,'2027-01-01','default.jpg','YM000021'),(22,'Telmisartan 40 mg Tablet','Cardio',50,70,'2027-01-01','default.jpg','YM000022'),(23,'Atorvastatin 10 mg Tablet','Cardio',60,80,'2027-01-01','default.jpg','YM000023'),(24,'Omeprazole 20 mg Capsule','Gastric',25,100,'2026-12-01','default.jpg','YM000024'),(25,'Ranitidine 150 mg Tablet','Gastric',20,80,'2026-12-01','default.jpg','YM000025'),(26,'ORS Powder Sachet','General',20,150,'2027-01-01','default.jpg','YM000026'),(27,'Betamethasone Cream 0.05%','Dermatology',40,59,'2026-12-01','default.jpg','YM000027'),(28,'Calamine Lotion','Dermatology',35,69,'2026-12-01','default.jpg','YM000028'),(29,'Ciprofloxacin Eye Drops','Eye',50,49,'2026-12-01','default.jpg','YM000029'),(30,'Timolol Eye Drops','Eye',60,40,'2026-12-01','default.jpg','YM000030'),(31,'Hydrogen Peroxide Solution','General',30,60,'2026-12-01','default.jpg','YM000031'),(32,'Ethyl Alcohol 70%','General',50,80,'2026-12-01','default.jpg','YM000032'),(33,'Paracetamol 500mg','Tablet',20,100,'2026-12-31',NULL,'YM000033'),(34,'Ibuprofen 400mg','Tablet',35,100,'2026-12-31',NULL,'YM000034'),(35,'Amoxicillin 500mg','Capsule',120,100,'2026-12-31',NULL,'YM000035'),(36,'Azithromycin 500mg','Tablet',150,100,'2026-12-31',NULL,'YM000036'),(37,'Cefixime 200mg','Tablet',180,100,'2026-12-31',NULL,'YM000037'),(38,'Ciprofloxacin 500mg','Tablet',80,100,'2026-12-31',NULL,'YM000038'),(39,'Metformin 500mg','Tablet',30,100,'2026-12-31',NULL,'YM000039'),(40,'Glimepiride 2mg','Tablet',45,100,'2026-12-31',NULL,'YM000040'),(41,'Amlodipine 5mg','Tablet',35,100,'2026-12-31',NULL,'YM000041'),(42,'Losartan 50mg','Tablet',60,100,'2026-12-31',NULL,'YM000042'),(43,'Atorvastatin 10mg','Tablet',80,100,'2026-12-31',NULL,'YM000043'),(44,'Rosuvastatin 10mg','Tablet',90,100,'2026-12-31',NULL,'YM000044'),(45,'Pantoprazole 40mg','Tablet',60,100,'2026-12-31',NULL,'YM000045'),(46,'Omeprazole 20mg','Capsule',50,100,'2026-12-31',NULL,'YM000046'),(47,'Rabeprazole 20mg','Tablet',65,100,'2026-12-31',NULL,'YM000047'),(48,'Domperidone 10mg','Tablet',40,100,'2026-12-31',NULL,'YM000048'),(49,'Ondansetron 4mg','Tablet',55,100,'2026-12-31',NULL,'YM000049'),(50,'Cetirizine 10mg','Tablet',25,100,'2026-12-31',NULL,'YM000050'),(51,'Levocetirizine 5mg','Tablet',30,100,'2026-12-31',NULL,'YM000051'),(52,'Montelukast 10mg','Tablet',90,100,'2026-12-31',NULL,'YM000052'),(53,'Dextromethorphan Syrup','Syrup',70,100,'2026-12-31',NULL,'YM000053'),(54,'Ambroxol Syrup','Syrup',60,100,'2026-12-31',NULL,'YM000054'),(55,'Salbutamol Inhaler','Inhaler',180,100,'2026-12-31',NULL,'YM000055'),(56,'Beclomethasone Inhaler','Inhaler',250,100,'2026-12-31',NULL,'YM000056'),(57,'Diclofenac 50mg','Tablet',30,100,'2026-12-31',NULL,'YM000057'),(58,'Paracetamol 650mg','Tablet',25,100,'2026-12-31',NULL,'YM000058'),(59,'Aspirin 75mg','Tablet',25,100,'2026-12-31',NULL,'YM000059'),(60,'Clopidogrel 75mg','Tablet',120,100,'2026-12-31',NULL,'YM000060'),(61,'Warfarin 5mg','Tablet',60,100,'2026-12-31',NULL,'YM000061'),(62,'Heparin Injection','Injection',200,100,'2026-12-31',NULL,'YM000062'),(63,'Tranexamic Acid 500mg','Tablet',90,100,'2026-12-31',NULL,'YM000063'),(64,'Vitamin C 500mg','Tablet',35,100,'2026-12-31',NULL,'YM000064'),(65,'Vitamin B Complex','Tablet',40,100,'2026-12-31',NULL,'YM000065'),(66,'Iron Folic Acid','Tablet',45,100,'2026-12-31',NULL,'YM000066'),(67,'Zinc Tablets','Tablet',30,100,'2026-12-31',NULL,'YM000067'),(68,'ORS Powder','Sachet',20,100,'2026-12-31',NULL,'YM000068'),(69,'Loperamide 2mg','Tablet',25,100,'2026-12-31',NULL,'YM000069'),(70,'Dicyclomine 20mg','Tablet',40,100,'2026-12-31',NULL,'YM000070'),(71,'Ranitidine 150mg','Tablet',30,100,'2026-12-31',NULL,'YM000071'),(72,'Sucralfate Syrup','Syrup',90,100,'2026-12-31',NULL,'YM000072'),(73,'Multivitamin Tablets','Tablet',60,100,'2026-12-31',NULL,'YM000073'),(74,'Calcium + Vitamin D3','Tablet',55,100,'2026-12-31',NULL,'YM000074'),(75,'Cough Syrup','Syrup',70,100,'2026-12-31',NULL,'YM000075'),(76,'Betadine Solution','Antiseptic',50,100,'2026-12-31',NULL,'YM000076'),(77,'Dettol Solution','Antiseptic',60,100,'2026-12-31',NULL,'YM000077'),(78,'Hydrogen Peroxide','Antiseptic',25,100,'2026-12-31',NULL,'YM000078'),(79,'Povidone Iodine Ointment','Ointment',80,100,'2026-12-31',NULL,'YM000079'),(80,'Neosporin Ointment','Ointment',90,100,'2026-12-31',NULL,'YM000080'),(81,'Clotrimazole Cream','Cream',75,100,'2026-12-31',NULL,'YM000081'),(82,'Ketoconazole Shampoo','Shampoo',180,100,'2026-12-31',NULL,'YM000082'),(83,'Minoxidil Solution','Hair Care',300,100,'2026-12-31',NULL,'YM000083'),(84,'Finasteride 1mg','Tablet',250,100,'2026-12-31',NULL,'YM000084'),(85,'Albendazole 400mg','Tablet',30,100,'2026-12-31',NULL,'YM000085'),(86,'Mebendazole 100mg','Tablet',25,100,'2026-12-31',NULL,'YM000086'),(87,'Ivermectin 12mg','Tablet',60,100,'2026-12-31',NULL,'YM000087'),(88,'Doxycycline 100mg','Tablet',70,100,'2026-12-31',NULL,'YM000088'),(89,'Linezolid 600mg','Tablet',400,100,'2026-12-31',NULL,'YM000089'),(90,'Vancomycin Injection','Injection',900,100,'2026-12-31',NULL,'YM000090'),(91,'Meropenem Injection','Injection',800,100,'2026-12-31',NULL,'YM000091'),(92,'Piperacillin Tazobactam','Injection',650,100,'2026-12-31',NULL,'YM000092'),(93,'Levofloxacin 500mg','Tablet',90,100,'2026-12-31',NULL,'YM000093'),(94,'Norfloxacin 400mg','Tablet',60,100,'2026-12-31',NULL,'YM000094'),(95,'Chlorpheniramine 4mg','Tablet',20,100,'2026-12-31',NULL,'YM000095'),(96,'Diphenhydramine Syrup','Syrup',50,100,'2026-12-31',NULL,'YM000096'),(97,'Guaifenesin Syrup','Syrup',65,100,'2026-12-31',NULL,'YM000097'),(98,'Activated Charcoal','Tablet',35,100,'2026-12-31',NULL,'YM000098'),(99,'Bisacodyl 5mg','Tablet',30,100,'2026-12-31',NULL,'YM000099'),(100,'Senna Tablets','Tablet',25,100,'2026-12-31',NULL,'YM000100'),(101,'Furosemide 40mg','Tablet',40,100,'2026-12-31',NULL,'YM000101'),(102,'Spironolactone 25mg','Tablet',45,100,'2026-12-31',NULL,'YM000102'),(103,'Digoxin 0.25mg','Tablet',60,100,'2026-12-31',NULL,'YM000103'),(104,'Sitagliptin 50mg','Tablet',400,100,'2026-12-31',NULL,'YM000104'),(105,'Vildagliptin 50mg','Tablet',380,100,'2026-12-31',NULL,'YM000105'),(106,'Dapagliflozin 10mg','Tablet',450,100,'2026-12-31',NULL,'YM000106'),(107,'Empagliflozin 10mg','Tablet',480,100,'2026-12-31',NULL,'YM000107'),(108,'Pioglitazone 15mg','Tablet',120,100,'2026-12-31',NULL,'YM000108'),(109,'Glipizide 5mg','Tablet',60,100,'2026-12-31',NULL,'YM000109'),(110,'Sertraline 50mg','Tablet',180,100,'2026-12-31',NULL,'YM000110'),(111,'Fluoxetine 20mg','Tablet',160,100,'2026-12-31',NULL,'YM000111'),(112,'Escitalopram 10mg','Tablet',170,100,'2026-12-31',NULL,'YM000112'),(113,'Venlafaxine 75mg','Tablet',220,100,'2026-12-31',NULL,'YM000113'),(114,'Duloxetine 30mg','Tablet',240,100,'2026-12-31',NULL,'YM000114'),(115,'Amitriptyline 25mg','Tablet',90,100,'2026-12-31',NULL,'YM000115'),(116,'Olanzapine 5mg','Tablet',300,100,'2026-12-31',NULL,'YM000116'),(117,'Risperidone 2mg','Tablet',250,100,'2026-12-31',NULL,'YM000117'),(118,'Quetiapine 100mg','Tablet',280,100,'2026-12-31',NULL,'YM000118'),(119,'Aripiprazole 10mg','Tablet',350,100,'2026-12-31',NULL,'YM000119'),(120,'Levothyroxine 50mcg','Tablet',60,100,'2026-12-31',NULL,'YM000120'),(121,'Carbimazole 10mg','Tablet',70,100,'2026-12-31',NULL,'YM000121'),(122,'Amiodarone 200mg','Tablet',150,100,'2026-12-31',NULL,'YM000122'),(123,'Propranolol 40mg','Tablet',90,100,'2026-12-31',NULL,'YM000123'),(124,'Atenolol 50mg','Tablet',80,100,'2026-12-31',NULL,'YM000124'),(125,'Tamsulosin 0.4mg','Tablet',150,100,'2026-12-31',NULL,'YM000125'),(126,'Sildenafil 50mg','Tablet',180,100,'2026-12-31',NULL,'YM000126'),(127,'Tadalafil 10mg','Tablet',200,100,'2026-12-31',NULL,'YM000127'),(128,'Dutasteride 0.5mg','Tablet',250,100,'2026-12-31',NULL,'YM000128'),(129,'Hydroxychloroquine 200mg','Tablet',150,100,'2026-12-31',NULL,'YM000129'),(130,'Artemether Lumefantrine','Tablet',180,100,'2026-12-31',NULL,'YM000130'),(131,'Atovaquone Proguanil','Tablet',500,100,'2026-12-31',NULL,'YM000131'),(132,'Roxithromycin 150mg','Tablet',120,100,'2026-12-31',NULL,'YM000132'),(133,'Clarithromycin 500mg','Tablet',160,100,'2026-12-31',NULL,'YM000133'),(134,'Erythromycin 250mg','Tablet',90,100,'2026-12-31',NULL,'YM000134'),(135,'Tetracycline 500mg','Tablet',80,100,'2026-12-31',NULL,'YM000135'),(136,'Minocycline 100mg','Tablet',110,100,'2026-12-31',NULL,'YM000136'),(137,'Gentamicin Injection','Injection',150,100,'2026-12-31',NULL,'YM000137'),(138,'Tobramycin Injection','Injection',180,100,'2026-12-31',NULL,'YM000138'),(139,'Amikacin Injection','Injection',200,100,'2026-12-31',NULL,'YM000139'),(140,'Streptomycin Injection','Injection',140,100,'2026-12-31',NULL,'YM000140'),(141,'Ceftriaxone 1g','Injection',250,100,'2026-12-31',NULL,'YM000141'),(142,'Cefotaxime 1g','Injection',220,100,'2026-12-31',NULL,'YM000142'),(143,'Cefuroxime 500mg','Tablet',180,100,'2026-12-31',NULL,'YM000143'),(144,'Cefpodoxime 200mg','Tablet',170,100,'2026-12-31',NULL,'YM000144'),(145,'Cefadroxil 500mg','Tablet',150,100,'2026-12-31',NULL,'YM000145'),(146,'Cloxacillin 500mg','Tablet',130,100,'2026-12-31',NULL,'YM000146'),(147,'Dicloxacillin 500mg','Tablet',140,100,'2026-12-31',NULL,'YM000147'),(148,'Penicillin V 250mg','Tablet',80,100,'2026-12-31',NULL,'YM000148'),(149,'Ampicillin 500mg','Capsule',90,100,'2026-12-31',NULL,'YM000149'),(150,'Sulbactam Injection','Injection',300,100,'2026-12-31',NULL,'YM000150'),(151,'Amoxiclav 625mg','Tablet',180,100,'2026-12-31',NULL,'YM000151'),(152,'Co-trimoxazole','Tablet',70,100,'2026-12-31',NULL,'YM000152'),(153,'Trimethoprim 160mg','Tablet',60,100,'2026-12-31',NULL,'YM000153'),(154,'Nitrofurantoin 100mg','Tablet',90,100,'2026-12-31',NULL,'YM000154'),(155,'Fosfomycin Sachet','Sachet',200,100,'2026-12-31',NULL,'YM000155'),(156,'Linezolid 300mg','Tablet',320,100,'2026-12-31',NULL,'YM000156'),(157,'Daptomycin Injection','Injection',900,100,'2026-12-31',NULL,'YM000157'),(158,'Colistin Injection','Injection',850,100,'2026-12-31',NULL,'YM000158'),(159,'Teicoplanin Injection','Injection',780,100,'2026-12-31',NULL,'YM000159'),(160,'Clindamycin 150mg','Tablet',110,100,'2026-12-31',NULL,'YM000160'),(161,'Metronidazole 200mg','Tablet',50,100,'2026-12-31',NULL,'YM000161'),(162,'Tinidazole 500mg','Tablet',80,100,'2026-12-31',NULL,'YM000162'),(163,'Secnidazole 1g','Tablet',120,100,'2026-12-31',NULL,'YM000163'),(164,'Albendazole Chewable','Tablet',35,100,'2026-12-31',NULL,'YM000164'),(165,'Praziquantel 600mg','Tablet',200,100,'2026-12-31',NULL,'YM000165'),(166,'Mebendazole Suspension','Syrup',40,100,'2024-01-31',NULL,'YM000166'),(167,'Artemisinin Combination','Tablet',180,100,'2026-12-31',NULL,'YM000167'),(168,'Quinine Sulphate','Tablet',150,100,'2026-12-31',NULL,'YM000168'),(169,'Primaquine 15mg','Tablet',90,100,'2026-12-31',NULL,'YM000169'),(170,'Chloroquine Phosphate','Tablet',100,100,'2026-12-31',NULL,'YM000170'),(171,'Atovaquone 250mg','Tablet',450,100,'2026-12-31',NULL,'YM000171'),(172,'Proguanil 100mg','Tablet',300,100,'2026-12-31',NULL,'YM000172'),(173,'Oseltamivir 75mg','Capsule',500,100,'2026-12-31',NULL,'YM000173'),(174,'Zanamivir Inhaler','Inhaler',650,100,'2026-12-31',NULL,'YM000174'),(175,'Remdesivir Injection','Injection',1200,100,'2026-12-31',NULL,'YM000175'),(176,'Favipiravir 200mg','Tablet',600,100,'2026-12-31',NULL,'YM000176'),(177,'Molnupiravir 200mg','Tablet',700,100,'2026-12-31',NULL,'YM000177'),(178,'Acyclovir 400mg','Tablet',150,100,'2026-12-31',NULL,'YM000178'),(179,'Valacyclovir 500mg','Tablet',300,100,'2026-12-31',NULL,'YM000179'),(180,'Ganciclovir Injection','Injection',900,100,'2026-12-31',NULL,'YM000180'),(181,'Famciclovir 250mg','Tablet',280,100,'2026-12-31',NULL,'YM000181'),(182,'Tenofovir Alafenamide','Tablet',500,100,'2026-12-31',NULL,'YM000182'),(183,'Ribavirin 200mg','Tablet',350,100,'2026-12-31',NULL,'YM000183'),(184,'Interferon Alfa Injection','Injection',1500,100,'2026-12-31',NULL,'YM000184'),(185,'Etanercept Injection','Injection',2000,100,'2026-12-31',NULL,'YM000185'),(186,'Adalimumab Injection','Injection',2500,100,'2026-12-31',NULL,'YM000186'),(187,'Infliximab Injection','Injection',3000,100,'2026-12-31',NULL,'YM000187'),(188,'Rituximab Injection','Injection',3500,100,'2026-12-31',NULL,'YM000188'),(189,'Bevacizumab Injection','Injection',4000,100,'2026-12-31',NULL,'YM000189'),(190,'Trastuzumab Injection','Injection',4500,100,'2026-12-31',NULL,'YM000190'),(191,'Epoetin Alfa Injection','Injection',800,100,'2026-12-31',NULL,'YM000191'),(192,'Darbepoetin Alfa','Injection',900,100,'2026-12-31',NULL,'YM000192'),(193,'Filgrastim Injection','Injection',700,100,'2026-12-31',NULL,'YM000193'),(194,'Pegfilgrastim Injection','Injection',1200,100,'2026-12-31',NULL,'YM000194'),(195,'Insulin Glargine','Injection',400,100,'2026-12-31',NULL,'YM000195'),(196,'Insulin Lispro','Injection',380,100,'2026-12-31',NULL,'YM000196'),(197,'Insulin Aspart','Injection',370,100,'2026-12-31',NULL,'YM000197'),(198,'Human Insulin','Injection',350,100,'2026-12-31',NULL,'YM000198'),(199,'Glucagon Injection','Injection',500,100,'2026-12-31',NULL,'YM000199'),(200,'Dexamethasone 4mg','Tablet',60,100,'2026-12-31',NULL,'YM000200'),(201,'Prednisone 20mg','Tablet',80,100,'2026-12-31',NULL,'YM000201'),(202,'Methylprednisolone 16mg','Tablet',120,100,'2026-12-31',NULL,'YM000202'),(203,'Betamethasone Injection','Injection',150,100,'2026-12-31',NULL,'YM000203'),(204,'Fluticasone Nasal Spray','Spray',200,100,'2026-12-31',NULL,'YM000204'),(205,'Budesonide Inhaler','Inhaler',250,100,'2026-12-31',NULL,'YM000205'),(206,'Formoterol Inhaler','Inhaler',300,100,'2026-12-31',NULL,'YM000206'),(207,'Salmeterol Inhaler','Inhaler',320,100,'2026-12-31',NULL,'YM000207'),(208,'Ipratropium Inhaler','Inhaler',280,100,'2026-12-31',NULL,'YM000208'),(209,'Theophylline 200mg','Tablet',90,100,'2026-12-31',NULL,'YM000209'),(210,'Montelukast 5mg','Tablet',80,100,'2026-12-31',NULL,'YM000210'),(211,'Zafirlukast 20mg','Tablet',100,100,'2026-12-31',NULL,'YM000211'),(212,'Azelastine Nasal Spray','Spray',150,100,'2026-12-31',NULL,'YM000212'),(213,'Olopatadine Eye Drops','Eye Drops',120,100,'2026-12-31',NULL,'YM000213'),(214,'Ketotifen Eye Drops','Eye Drops',90,100,'2026-12-31',NULL,'YM000214'),(215,'Brinzolamide Eye Drops','Eye Drops',180,100,'2026-12-31',NULL,'YM000215'),(216,'Acetaminophen Injection','Injection',100,100,'2026-12-31',NULL,'YM000216'),(217,'Ketorolac Injection','Injection',120,100,'2026-12-31',NULL,'YM000217'),(218,'Tramadol Injection','Injection',150,100,'2026-12-31',NULL,'YM000218'),(219,'Morphine Injection','Injection',300,100,'2026-12-31',NULL,'YM000219'),(220,'Fentanyl Patch','Patch',500,100,'2026-12-31',NULL,'YM000220'),(221,'Lidocaine Injection','Injection',80,100,'2026-12-31',NULL,'YM000221'),(222,'Bupivacaine Injection','Injection',90,100,'2026-12-31',NULL,'YM000222'),(223,'Ropivacaine Injection','Injection',110,100,'2026-12-31',NULL,'YM000223'),(224,'Nalbuphine Injection','Injection',150,100,'2026-12-31',NULL,'YM000224'),(225,'Diclofenac Gel','Gel',70,100,'2026-12-31',NULL,'YM000225'),(226,'Ketoprofen Gel','Gel',80,100,'2026-12-31',NULL,'YM000226'),(227,'Mupirocin Ointment','Ointment',120,100,'2026-12-31',NULL,'YM000227'),(228,'Silver Sulfadiazine Cream','Cream',150,100,'2026-12-31',NULL,'YM000228'),(229,'Hydrocortisone Cream','Cream',65,100,'2026-12-31',NULL,'YM000229'),(230,'Clobetasol Cream','Cream',90,100,'2026-12-31',NULL,'YM000230'),(231,'Tacrolimus Ointment','Ointment',200,100,'2026-12-31',NULL,'YM000231'),(232,'Pimecrolimus Cream','Cream',180,100,'2026-12-31',NULL,'YM000232'),(233,'Terbinafine Cream','Cream',140,100,'2026-12-31',NULL,'YM000233'),(234,'Luliconazole Cream','Cream',160,100,'2026-12-31',NULL,'YM000234'),(235,'Sertaconazole Cream','Cream',150,100,'2026-12-31',NULL,'YM000235'),(236,'Sodium Chloride Injection','Injection',50,100,'2026-12-31',NULL,'YM000236'),(237,'Dextrose 5% IV','IV Fluid',60,100,'2026-12-31',NULL,'YM000237'),(238,'Ringer Lactate','IV Fluid',70,100,'2026-12-31',NULL,'YM000238'),(239,'Normal Saline','IV Fluid',50,100,'2026-12-31',NULL,'YM000239'),(240,'Potassium Chloride','Injection',80,100,'2026-12-31',NULL,'YM000240'),(241,'Magnesium Sulphate','Injection',90,100,'2026-12-31',NULL,'YM000241'),(242,'Calcium Gluconate','Injection',100,100,'2026-12-31',NULL,'YM000242'),(243,'Sodium Bicarbonate Injection','Injection',70,100,'2026-12-31',NULL,'YM000243'),(244,'Heparin Low Molecular Weight','Injection',300,100,'2026-12-31',NULL,'YM000244'),(245,'Enoxaparin Injection','Injection',350,100,'2026-12-31',NULL,'YM000245'),(246,'Gliclazide 80mg','Diabetes',50,100,'2026-12-31',NULL,'YM000246'),(247,'Ofloxacin 200mg','Antibiotic',70,100,'2026-12-31',NULL,'YM000247'),(248,'Clindamycin 300mg','Antibiotic',120,100,'2026-12-31',NULL,'YM000248'),(249,'Metronidazole 400mg','Antibiotic',45,100,'2026-12-31',NULL,'YM000249'),(250,'Rifampicin 450mg','Anti-TB',120,100,'2026-12-31',NULL,'YM000250'),(251,'Isoniazid 300mg','Anti-TB',60,100,'2026-12-31',NULL,'YM000251'),(252,'Ethambutol 800mg','Anti-TB',70,100,'2026-12-31',NULL,'YM000252'),(253,'Pyrazinamide 500mg','Anti-TB',80,100,'2026-12-31',NULL,'YM000253'),(254,'Tenofovir 300mg','Antiviral',350,100,'2026-12-31',NULL,'YM000254'),(255,'Lamivudine 300mg','Antiviral',200,100,'2026-12-31',NULL,'YM000255'),(256,'Zidovudine 300mg','Antiviral',300,100,'2026-12-31',NULL,'YM000256'),(257,'Efavirenz 600mg','Antiviral',450,100,'2026-12-31',NULL,'YM000257'),(258,'Dolutegravir 50mg','Antiviral',600,100,'2026-12-31',NULL,'YM000258'),(259,'Fluconazole 150mg','Antifungal',90,100,'2026-12-31',NULL,'YM000259'),(260,'Itraconazole 100mg','Antifungal',180,100,'2026-12-31',NULL,'YM000260'),(261,'Terbinafine 250mg','Antifungal',150,100,'2026-12-31',NULL,'YM000261'),(262,'Griseofulvin 500mg','Antifungal',200,100,'2026-12-31',NULL,'YM000262'),(263,'Prednisolone 10mg','Steroid',90,100,'2026-12-31',NULL,'YM000263'),(264,'Hydrocortisone','Steroid',65,100,'2026-12-31',NULL,'YM000264'),(265,'Fexofenadine 120mg','Antihistamine',90,100,'2026-12-31',NULL,'YM000265'),(266,'Sucralfate','GI',90,100,'2026-12-31',NULL,'YM000266'),(267,'Calcium + D3','Supplement',55,100,'2026-12-31',NULL,'YM000267'),(268,'Chloroquine 250mg','Antimalarial',100,100,'2026-12-31',NULL,'YM000268'),(269,'Remdesivir','Injection',1200,100,'2026-12-31',NULL,'YM000269'),(270,'Meropenem 1g','Injection',800,100,'2026-12-31',NULL,'YM000270'),(271,'Vancomycin','Injection',900,100,'2026-12-31',NULL,'YM000271'),(272,'Gentamicin','Injection',150,100,'2026-12-31',NULL,'YM000272'),(273,'Amikacin','Injection',200,100,'2026-12-31',NULL,'YM000273'),(274,'Heparin','Injection',200,100,'2026-12-31',NULL,'YM000274'),(275,'Enoxaparin','Injection',350,100,'2026-12-31',NULL,'YM000275'),(276,'Mupirocin','Ointment',120,100,'2026-12-31',NULL,'YM000276'),(277,'Ketoconazole Cream','Cream',90,100,'2026-12-31',NULL,'YM000277'),(278,'Silver Sulfadiazine','Cream',150,100,'2026-12-31',NULL,'YM000278'),(279,'Minoxidil','Topical',300,100,'2026-12-31',NULL,'YM000279'),(280,'Dutasteride','Urology',250,100,'2026-12-31',NULL,'YM000280'),(281,'Tamsulosin','Urology',150,100,'2026-12-31',NULL,'YM000281'),(282,'Sildenafil','Urology',180,100,'2026-12-31',NULL,'YM000282'),(283,'Tadalafil','Urology',200,100,'2026-12-31',NULL,'YM000283'),(284,'Acetaminophen 650mg','Analgesic',25,100,'2026-12-31',NULL,'YM000284'),(285,'Naproxen 250mg','Analgesic',40,100,'2026-12-31',NULL,'YM000285'),(286,'Etodolac 300mg','Analgesic',55,100,'2026-12-31',NULL,'YM000286'),(287,'Ketorolac 10mg','Analgesic',60,100,'2026-12-31',NULL,'YM000287'),(288,'Meloxicam 7.5mg','Analgesic',70,100,'2026-12-31',NULL,'YM000288'),(289,'Piroxicam 20mg','Analgesic',65,100,'2026-12-31',NULL,'YM000289'),(290,'Celecoxib 200mg','Analgesic',120,100,'2026-12-31',NULL,'YM000290'),(291,'Etoricoxib 90mg','Analgesic',140,100,'2026-12-31',NULL,'YM000291'),(292,'Indomethacin 25mg','Analgesic',50,100,'2026-12-31',NULL,'YM000292'),(293,'Aceclofenac 100mg','Analgesic',45,100,'2026-12-31',NULL,'YM000293'),(294,'Lactulose Syrup','GI',120,100,'2026-12-31',NULL,'YM000294'),(295,'Pantoprazole 20mg','Gastric',55,100,'2026-12-31',NULL,'YM000295'),(296,'Esomeprazole 40mg','Gastric',80,100,'2026-12-31',NULL,'YM000296'),(297,'Dexlansoprazole 30mg','Gastric',100,100,'2025-12-15',NULL,'YM000297'),(298,'Cimetidine 200mg','GI',35,100,'2026-12-31',NULL,'YM000298'),(299,'Famotidine 20mg','GI',40,100,'2026-12-31',NULL,'YM000299'),(300,'Rifaximin 200mg','Antibiotic',200,100,'2026-12-31',NULL,'YM000300'),(301,'Spiramycin 3M IU','Antibiotic',250,100,'2026-12-31',NULL,'YM000301'),(302,'Cefaclor 250mg','Antibiotic',120,100,'2026-12-31',NULL,'YM000302'),(303,'Cefuroxime Axetil 500mg','Antibiotic',180,100,'2026-12-31',NULL,'YM000303'),(304,'Piperacillin + Tazobactam','Antibiotic',500,100,'2026-12-31',NULL,'YM000304'),(305,'Imipenem 500mg','Antibiotic',700,100,'2026-12-31',NULL,'YM000305'),(306,'Ertapenem 1g','Antibiotic',800,100,'2026-12-31',NULL,'YM000306'),(307,'Doripenem 500mg','Antibiotic',850,100,'2026-12-31',NULL,'YM000307'),(308,'Tigecycline 50mg','Antibiotic',900,100,'2026-12-31',NULL,'YM000308'),(309,'Polymyxin B','Antibiotic',950,100,'2026-12-31',NULL,'YM000309'),(310,'Bacitracin Ointment','Antibiotic',60,100,'2026-12-31',NULL,'YM000310'),(311,'Neomycin Cream','Antibiotic',55,100,'2026-12-31',NULL,'YM000311'),(312,'Ofloxacin Eye Drops','Eye Drops',70,100,'2026-12-31',NULL,'YM000312'),(313,'Moxifloxacin Eye Drops','Eye Drops',120,100,'2026-12-31',NULL,'YM000313'),(314,'Tobramycin Eye Drops','Eye Drops',100,100,'2026-12-31',NULL,'YM000314'),(315,'Atropine Eye Drops','Eye Drops',90,100,'2026-12-31',NULL,'YM000315'),(316,'Cyclopentolate Eye Drops','Eye Drops',110,100,'2026-12-31',NULL,'YM000316'),(317,'Brimonidine Eye Drops','Eye Drops',200,100,'2026-12-31',NULL,'YM000317'),(318,'Latanoprost Eye Drops','Eye Drops',300,100,'2026-12-31',NULL,'YM000318'),(319,'Travoprost Eye Drops','Eye Drops',320,100,'2026-12-31',NULL,'YM000319'),(320,'Dorzolamide Eye Drops','Eye Drops',180,100,'2026-12-31',NULL,'YM000320'),(321,'Brinzolamide + Timolol','Eye Drops',250,100,'2026-12-31',NULL,'YM000321'),(322,'Betaxolol Eye Drops','Eye Drops',160,100,'2026-12-31',NULL,'YM000322'),(323,'Ketorolac Eye Drops','Eye Drops',90,100,'2026-12-31',NULL,'YM000323'),(324,'Quetiapine 50mg','Psychiatric',150,100,'2026-12-31',NULL,'YM000324'),(325,'Clozapine 25mg','Psychiatric',180,100,'2026-12-31',NULL,'YM000325'),(326,'Paroxetine 20mg','Psychiatric',130,100,'2026-12-31',NULL,'YM000326'),(327,'Nortriptyline 10mg','Psychiatric',90,100,'2026-12-31',NULL,'YM000327'),(328,'Diazepam 5mg','Psychiatric',60,100,'2026-12-31',NULL,'YM000328'),(329,'Clonazepam 0.5mg','Psychiatric',70,100,'2026-12-31',NULL,'YM000329'),(330,'Lorazepam 1mg','Psychiatric',65,100,'2026-12-31',NULL,'YM000330'),(331,'Alprazolam 0.5mg','Psychiatric',80,100,'2026-12-31',NULL,'YM000331'),(332,'Zolpidem 10mg','Sleep',90,100,'2026-12-31',NULL,'YM000332'),(333,'Zopiclone 7.5mg','Sleep',85,100,'2026-12-31',NULL,'YM000333'),(334,'Melatonin 3mg','Sleep',60,100,'2026-12-31',NULL,'YM000334'),(335,'Hydroxyzine 25mg','Antihistamine',70,100,'2026-12-31',NULL,'YM000335'),(336,'Diphenhydramine 25mg','Antihistamine',30,100,'2026-12-31',NULL,'YM000336'),(337,'Rupatadine 10mg','Antihistamine',90,100,'2026-12-31',NULL,'YM000337'),(338,'Desloratadine 5mg','Antihistamine',80,100,'2026-12-31',NULL,'YM000338'),(339,'Cough Syrup Dextromethorphan','Cough',60,100,'2026-12-31',NULL,'YM000339'),(340,'Ambroxol 30mg','Cough',55,100,'2026-12-31',NULL,'YM000340'),(341,'Bromhexine 8mg','Cough',50,100,'2026-12-31',NULL,'YM000341'),(342,'Guaifenesin 100mg','Cough',45,100,'2026-12-31',NULL,'YM000342'),(343,'Levosalbutamol Syrup','Respiratory',70,100,'2026-12-31',NULL,'YM000343'),(344,'Budesonide Respules','Inhaler',180,100,'2026-12-31',NULL,'YM000344'),(345,'Ipratropium Bromide','Inhaler',150,100,'2026-12-31',NULL,'YM000345'),(346,'Tiotropium Inhaler','Inhaler',300,100,'2026-12-31',NULL,'YM000346'),(347,'Fluticasone Inhaler','Inhaler',280,100,'2026-12-31',NULL,'YM000347'),(348,'Montelukast + Levocetirizine','Respiratory',100,100,'2026-12-31',NULL,'YM000348'),(349,'ORS Electrolyte Powder','Supplement',20,100,'2026-12-31',NULL,'YM000349'),(350,'Biotin Tablets','Supplement',60,100,'2026-12-31',NULL,'YM000350'),(351,'Vitamin D3 60000 IU','Supplement',90,100,'2026-12-31',NULL,'YM000351'),(352,'Omega 3 Capsules','Supplement',120,100,'2026-12-31',NULL,'YM000352'),(353,'Coenzyme Q10','Supplement',250,100,'2026-12-31',NULL,'YM000353'),(354,'Glucosamine Sulphate','Supplement',180,100,'2026-12-31',NULL,'YM000354'),(355,'Chondroitin Sulphate','Supplement',200,100,'2026-12-31',NULL,'YM000355'),(356,'Lycopene Capsules','Supplement',150,100,'2026-12-31',NULL,'YM000356'),(357,'Silymarin 140mg','Liver',120,100,'2026-12-31',NULL,'YM000357'),(358,'Ursodeoxycholic Acid','Liver',180,100,'2026-12-31',NULL,'YM000358'),(359,'Domperidone + Pantoprazole','Gastric',90,100,'2026-12-31',NULL,'YM000359'),(360,'Ondansetron Oral Film','Gastric',70,100,'2026-12-31',NULL,'YM000360'),(361,'Lansoprazole 30mg','Gastric',85,100,'2026-12-31',NULL,'YM000361'),(362,'Magaldrate Syrup','Gastric',60,100,'2026-12-31',NULL,'YM000362'),(363,'Sucralfate Suspension','Gastric',95,100,'2026-12-31',NULL,'YM000363'),(364,'ORS Zinc Combination','Supplement',35,100,'2026-12-31',NULL,'YM000364'),(365,'Permethrin Cream','Skin',90,100,'2026-12-31',NULL,'YM000365'),(366,'Clindamycin Gel','Skin',80,100,'2026-12-31',NULL,'YM000366'),(367,'Adapalene Gel','Skin',150,100,'2026-05-07',NULL,'YM000367'),(368,'Tretinoin Cream','Skin',200,100,'2026-12-31',NULL,'YM000368'),(369,'Benzoyl Peroxide','Skin',120,100,'2026-12-31',NULL,'YM000369'),(370,'Hydroquinone Cream','Skin',180,100,'2026-12-31',NULL,'YM000370'),(1217,'Paracetamol 650','Tablet',35,0,'2026-01-28',NULL,'YM001217'),(1218,'Crocin Advance','Tablet',25,0,'2026-05-30',NULL,'YM001218'),(1219,'paracetamol 650','medicine',35,12,'2026-05-07',NULL,'YM001219'),(1220,'Unknown Medicine','General',0,10,NULL,'/static/uploads/1778490085.240985.jpg','YM001220'),(1221,'Unknown Medicine','General',0,10,NULL,'/static/uploads/1778490154.777258.jpg','YM001221'),(1222,'Unknown Medicine','General',0,10,NULL,'/static/uploads/1778490323.853751.jpg','YM001222'),(1223,'Unknown Medicine','General',0,10,NULL,'/static/uploads/1778490348.312042.jpg','YM001223'),(1224,'Iodex','Lotion',92,100,'2026-10-01',NULL,'89000014');
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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_items`
--

LOCK TABLES `order_items` WRITE;
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
INSERT INTO `order_items` VALUES (1,1,2,4,20),(2,2,28,3,35),(3,3,2,2,20),(4,3,4,2,10),(5,3,13,1,40),(6,4,2,2,20),(7,5,3,2,30),(8,6,3,1,30),(9,7,3,2,30);
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
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (1,3,80,'2026-05-25 13:58:35','Delivered',NULL),(2,3,105,'2026-05-27 11:15:14','Cancelled',NULL),(3,3,100,'2026-06-01 10:15:05','Delivered',NULL),(4,3,40,'2026-06-01 15:13:59','Delivered',NULL),(5,3,60,'2026-06-02 08:33:30','Cancelled',NULL),(6,3,30,'2026-06-02 08:33:46','Pending',NULL),(7,3,60,'2026-06-03 15:27:17','Pending','static/uploads/1780500437.665901_Paracetamol_Syrup_125_mg-5ml.jpeg');
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prescription_requests`
--

DROP TABLE IF EXISTS `prescription_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prescription_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `prescription_image` varchar(255) DEFAULT NULL,
  `ocr_text` text,
  `detected_medicines` text,
  `status` varchar(50) DEFAULT 'Pending Review',
  `staff_note` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `reviewed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prescription_requests`
--

LOCK TABLES `prescription_requests` WRITE;
/*!40000 ALTER TABLE `prescription_requests` DISABLE KEYS */;
INSERT INTO `prescription_requests` VALUES (1,3,'user_3_1780503999.166781_Paracetamol_Syrup_125_mg-5ml.jpeg','','','Pending Review',NULL,'2026-06-03 16:26:39',NULL),(2,3,'user_3_1780504208.08775_1000081003.jpg','','','Pending Review',NULL,'2026-06-03 16:30:08',NULL),(3,3,'user_3_1780504442.214169_1000081003.jpg','','','Pending Review',NULL,'2026-06-03 16:34:02',NULL),(4,3,'user_3_1780510744.170117_Paracetamol_Syrup_125_mg-5ml.jpeg','','','Pending Review',NULL,'2026-06-03 18:19:04',NULL);
/*!40000 ALTER TABLE `prescription_requests` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Admin','admin@gmail.com','9999999999','Virar','owner','admin123','scrypt:32768:8:1$tWGGKrfzcPbwjHof$5b009e7b66a6e87d7ba79e9bce4312dc241fb380e8c65c855bf848e36643c6b99c580316d58b1091f7ca364826326b0c44b3be95b6b48246fdb6906b43a169ca'),(2,'Staff','staff@gmail.com','7498513789','Virar','staff','staff123','scrypt:32768:8:1$nQmtMKpc3PeFUHYl$3c4cca15e80077063af6823a828b9b7342fa89440d1af10a237e2a1b117437116c24e720f1146bef184e4cf8b5bab7d95a66248297a7ed4954c8428094ebba36'),(3,'Customer','customer@gmail.com','7498513789','Virar','customer','customer123','scrypt:32768:8:1$8RNv4oBOTDU6XtXQ$4f485dda9ddbf688f41e8185524d7ab717e3fff72f7d0225d1f6c2e9d1f57f88b147decd44f561b1b5c6bd4dbbcc675a0435d0e58332b0f2c43e048f91ba2833'),(4,'Sujal ','katkarsujal3@gmail.com','7498513789','virar west , yashwant nagar, sky City housing society, H-1205','staff',NULL,'scrypt:32768:8:1$4aOmxO55eOiDxf0n$b978a4d4f9bbd5ff04e141ddcc13159fc0c996ab2b7d969536c7ff4bd58345f3a5cbab256a022ea0bdeaa838eee0977e184b486533d262883f0f57596ed63917'),(5,'metaAI','testcustomer@yuvrajmedical.co.in','123','123','customer',NULL,'scrypt:32768:8:1$um5ZfQgMl6Frh1pt$fc16e1e05bbe9d918698b30c9aea961521bdcd1a74660477cae6624a0fb0b0a62b36e5096ac94085cd18f8eee5083df32323426210f0db96da3e8d7470eea696');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-04 15:16:37
