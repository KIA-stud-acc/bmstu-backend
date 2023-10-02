from django.shortcuts import render
import psycopg2
conn = psycopg2.connect(dbname="DAG", host="localhost", user="admin", password="admin", port="5432")
cursor = conn.cursor()
allItems = [
            {'name': "Памятник у храма христа спасителя",
             'src': 'https://avatars.dzeninfra.ru/get-zen_doc/198938/pub_5b7be219c3c1aa00aac7c4f2_5b7be25760eb2700a9ad95fc/scale_1200', 'id': 1,
             'results': [{'case':"Памятник Александра II: Великий Миротворец", 'votes':1234}, {'case':"Александр II: Освободитель народов", 'votes':3214}, {'case':"Памятник Александра II: Император-Реформатор", 'votes':123}],
             'desc':'Импозантный монумент, воздвигнутый в честь императора Александра II, отражающий его роль как символа мира, свободы и реформ.'},
            {'name': "Торговый центр в Московской области",
             'src': "https://puteshestviepomiru.ru/wp-content/uploads/2021/10/17bd7fdc-d5d3-4dc4-94a6-05d26d744369.jpg", 'id':2,
             'results': [{'case':'Метрополис', 'votes':3455}, {'case':'Городский Ландшафт', 'votes':45456}, {'case':'Мегаполис Шопинга', 'votes':39782}],
             'desc':'Современный торговый комплекс, предоставляющий разнообразие товаров и услуг, созданный для удовлетворения потребностей покупателей и посетителей.'},
            {'name': "Сквер на улице Колотушкина",
             'src': "https://ландшафтныйдом.рф/wp-content/uploads/2022/03/ozelenenie-skverov-3.jpeg", 'id': 3,
             'results': [{'case':'Зеленый Уголок', 'votes':21}, {'case':'Оазис Впечатлений', 'votes':35}, {'case':'Уголок Природы', 'votes':12}],
             'desc':'Ухоженный зеленый сквер, названный в честь улицы Колотушкина, служащий отличным местом для отдыха и прогулок в природной атмосфере.'},
        ]

def voteList(request, sear = "", items = allItems):

    selItems = []
    if sear != "":
        for i in items:
            if sear in i['name']:
                selItems.append(i)
    else: selItems = items
    return render(request, 'voteList.html', {'data': {
        'voteList': selItems,
        'src' : sear
    }})

def search(request):
    delId = request.POST.get("del", -1)
    if delId == -1:
        try:
            searchQuery = request.GET['text']
        except:
            searchQuery = ''
    else:
        searchQuery = ''
        cursor.execute(f"update \"name options\" set status = 'удалён' where id = {delId}")


    return voteList(request, searchQuery)

def getVoting(request, id, items = allItems):
    return render(request, 'voting.html', {'data':items[id-1]})
# Create your views here.
