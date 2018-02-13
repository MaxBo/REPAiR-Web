import os
fn = os.path.join('tmp', 'artifacts', 'test.txt')
text_file = open(fn, "w")
text_file.write("string")
text_file.close()
