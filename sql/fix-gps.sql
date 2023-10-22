CREATE PROCEDURE UpdatePlaceEstimates() BEGIN DECLARE bDone INT;
DECLARE target_id INT;
DECLARE target_date DATETIME;
DECLARE other_id INT;
DECLARE other_date DATETIME;
DECLARE reallyDone INT;
DECLARE curs CURSOR FOR 
SELECT 
  id, 
  taken_at 
FROM 
  photos 
WHERE 
  place_src = 'estimate';
DECLARE CONTINUE HANDLER FOR NOT FOUND 
SET 
  bDone = 1;
OPEN curs;
SET 
  reallyDone = 0;
SET 
  bDone = 0;
REPEAT FETCH curs INTO target_id, 
target_date;
IF bDone = 1 THEN 
SET 
  reallyDone = 1;
END IF;
SET 
  other_id = NULL;
SET 
  other_date = NULL;
SELECT 
  p.id, 
  p.taken_at INTO other_id, 
  other_date 
FROM 
  photos p 
WHERE 
  p.place_src = 'meta' 
  and p.taken_at >= DATE_ADD(target_date, INTERVAL -4 HOUR) 
  and p.taken_at <= DATE_ADD(target_date, INTERVAL 4 HOUR) 
LIMIT 
  1;
SELECT 
  target_id, 
  target_date, 
  other_id, 
  other_date;
SET 
  bDone = 0;
IF (other_id IS NULL) THEN 
UPDATE 
  photos 
SET 
  photo_country = 'zz', 
  place_id = 'zz', 
  place_src = '', 
  photo_altitude = 0, 
  photo_lat = 0, 
  photo_lng = 0 
WHERE 
  id = target_id;
END IF;
UNTIL reallyDone END REPEAT;
CLOSE curs;
END //
