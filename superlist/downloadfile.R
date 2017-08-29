library(RCurl)
txt = read_file("list.txt")
txt_list = strsplit(as.vector(txt),'\n')
length(txt_list[[1]])          
for (i in 1:length(txt_list[[1]]))
{
  URL <- paste0("https://pdf.hres.ca/dpd_pm/",txt_list[[1]][i])
  print(URL)
  file <- paste0('/home/hjiang/superlist/pdf_folder/',txt_list[[1]][i])
  print(file)
  download.file(URL,file)
}
    