<?php

$Menu=array(
  array("About","index.php"),
  array("News","news.php"),
  array("Download","http://sourceforge.net/projects/impressive/files/Impressive/"),
  array("Documentation","manual.php"),
  array("FAQ","faq.php")
);

$Quotes=array(
  "makes even the dullest|presentation look bright",
  "so convincing that your|audience will believe everything",
  "impressing your audience|has never been that easy",
  "the simplest way of keeping|your audience from yawning",
  "the Chuck Norris|of presentation software",
  "the name|actually makes sense"
);

?><!DOCTYPE html>
<html><head>
<title>Impressive</title>
<link rel="stylesheet" href="style.css" type="text/css" />
</head><body>

<div id="headl"><div id="headr"><div id="quote">&ldquo;<?php
srand(time());
echo str_replace("|","&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br />",$Quotes[rand()%count($Quotes)]);
?>&rdquo;</div></div></div>

<table id="menu"><tr>
<?php
$self=basename($_SERVER['PHP_SELF']);
for($i=0; $i<=count($Menu); $i++) {
  list($title,$url)=$Menu[$i];
  if($url==$self) echo "<td><div id=\"currentitem\">";
             else echo "<td><a href=\"$url\" class=\"menuitem\">";
  echo "<div class=\"l\"><div class=\"r\"><div class=\"c\">$title</div></div></div>";
  if($url==$self) echo "</div></td>\n";
             else echo "</a></td>\n";
}
?>
</tr></table>

<div id="content">
