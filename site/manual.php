<?php include("menu.php"); ?>

<h1>Impressive Documentation</h1>

<?php
  $fd=@fopen("impressive.html","r");
  $data=explode("<!--VERSION-->",@fread($fd,1024*1024));
  @fclose($fd);
  $data=explode("<!--END-->",$data[1]);
  echo $data[0];
  $data=explode("<!--EOT-->",$data[1]);
?>

<p class="note">You can <a href="impressive.html">download</a> this document for offline reading or <a href="javascript:window.print();">print</a> it.</p>

<?php echo $data[0]; ?>

</div></body></html>
