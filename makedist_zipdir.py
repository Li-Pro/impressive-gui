from pathlib  import Path
from zipfile  import ZipFile, ZIP_DEFLATED
import sys

if not (len(sys.argv) >= 3):
	raise Exception('argument error.')

out_path = Path(sys.argv[1])
in_path = Path(sys.argv[2])

print('Archiving {} -> {}'.format(in_path.resolve(), out_path.resolve()))

# requires module zlib
with ZipFile(out_path, compression=ZIP_DEFLATED, mode='w', compresslevel=9) as outfile:
	for file in in_path.glob('**/*'):
		outfile.write(file.resolve(), arcname=file.relative_to(in_path))