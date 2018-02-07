import os
fn = os.path.join(os.path.dirname(__file__), 'artifacts', 'test.txt')
text_file = open(fn, "w")
text_file.write("string")
text_file.close()
