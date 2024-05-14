<html>

<?php

// this script will display files by folder name day date as split YYYY/MM/DD and file name location ./ftp_files/$date/$location as chosen in the dropdown selection submit, with no date given defaulting to the current date
// for example ./ftp/2024/05/13/camden_00_20240513005106.jpg
// this date/day folder and filename convention is generated from Reolink camera scheduled periodic ftp push to the server

$params = $_REQUEST;

$location = isset($params['location']) && $params['location'] != '' ? $params['location'] : 'none';
$start_date = isset($params['start_date']) && $params['start_date'] != '' && $params['start_date'] != 'Select date' ? $params['start_date'] : 'none';

?>

<head>
<title>Camera photos</title>

<script
  src="https://code.jquery.com/jquery-3.5.1.min.js"
  integrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0="
  crossorigin="anonymous"></script>

    <!-- Bootstrap core CSS -->

    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">

    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>

    <!-- Custom fonts for this template -->
    <link href="https://fonts.googleapis.com/css?family=Lato:300,400,700,300italic,400italic,700italic" rel="stylesheet" type="text/css">

</head>


<script src="https://cdn.jsdelivr.net/npm/gijgo@1.9.10/js/gijgo.min.js" type="text/javascript"></script>
<link href="https://cdn.jsdelivr.net/npm/gijgo@1.9.10/css/gijgo.min.css" rel="stylesheet" type="text/css" />

<div class="row">
<div class="col-1">
Location<br/>
<select name="locationChoice" id="locationID">
  <option value="none">Select location...</option>
  <option value="whaley">whaley</option>
  <option value="Hoboken">Hoboken</option>
  <option value="RISE E1 Outdoor">RISE E1 Outdoor</option>
  <option value="camden">camden</option>
</select>
</div>


<div class="col-1">
  Date(YYYY/MM/DD)<input type="text" id="datepicker_start" onfocus="if (this.value == 'Select date') { this.value=''; }" width="150">
</div>

</div>

<input type="button" value="Submit" class="homebutton" id="locationChoice"
onClick="document.location.href='./index.php?location='+document.getElementById('locationID').value+'&start_date='+document.getElementById('datepicker_start').value" />

<br/>
<hr>

<script>
//more compact - but overrides bottom orientation - uiLibrary: 'bootstrap4'
$('#datepicker_start').datepicker({
  format: "yyyy/mm/dd",
  orientation: 'bottom'
});
document.getElementById("datepicker_start").value = "Select date";

//document.getElementById("locationID").value = "whaley";
document.getElementById("locationID").value = "<?php echo $location; ?>";
</script>


<?php

if ($start_date == 'none') {

date_default_timezone_set('America/New_York');
//$date = date('Y/m/d h:i:s a', time());
$date = date('Y/m/d', time());
//echo $date;
}
else { $date = $start_date; }


$dirname = "./ftp_files/$date/$location";
//echo $dirname;
$images = array_reverse(glob($dirname."*.jpg"));

$lines = 0;
foreach($images as $image) {
    echo '<img src="'.$image.'" height=500 width=665 onclick="this.requestFullscreen()" />';
    $lines++;
    if ($lines == 4) {
        echo '<br />';
    }
}

?>

</html>
