import os
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsExpression, QgsExpressionContext, QgsExpressionContextUtils
from PyQt5.QtCore import QVariant

# Caminhos para as pastas
caminho_propriedades = r"C:\Users"
caminho_alertas = r"C:\Users"

# Função para encontrar o primeiro arquivo .shp na pasta especificada
def encontrar_primeiro_shapefile(caminho_pasta):
    for filename in os.listdir(caminho_pasta):
        if filename.endswith(".shp"):
            return os.path.join(caminho_pasta, filename)
    return None

# Carregar a camada de propriedades
shapefile_propriedades = encontrar_primeiro_shapefile(caminho_propriedades)
if shapefile_propriedades:
    camada_propriedades = QgsVectorLayer(shapefile_propriedades, "propriedades", "ogr")
    if camada_propriedades.isValid():
        QgsProject.instance().addMapLayer(camada_propriedades)
    else:
        print("Camada 'propriedades' falhou ao carregar.")
else:
    print("Nenhum arquivo .shp encontrado na pasta 'propriedades'.")

# Carregar a camada de alertas
shapefile_alertas = encontrar_primeiro_shapefile(caminho_alertas)
if shapefile_alertas:
    camada_alertas = QgsVectorLayer(shapefile_alertas, "alertas", "ogr")
    if camada_alertas.isValid():
        QgsProject.instance().addMapLayer(camada_alertas)
    else:
        print("Camada 'alertas' falhou ao carregar.")
else:
    print("Nenhum arquivo .shp encontrado na pasta 'alertas'.")

# Certificar-se de que ambas as camadas foram carregadas corretamente antes de prosseguir
if camada_propriedades.isValid() and camada_alertas.isValid():
    # Definir os parâmetros para a ferramenta de interseção
    params = {
        'INPUT': camada_propriedades,
        'OVERLAY': camada_alertas,
        'OUTPUT': 'memory:'  # Salvar resultado na memória
    }

    # Executar a ferramenta de interseção
    resultado = processing.run('qgis:intersection', params)

    # Acessar a camada de saída da interseção
    camada_saida = resultado['OUTPUT']

    # Definir um nome personalizado para a camada de saída
    nome_camada_saida = "Sobreposição com alertas"
    camada_saida.setName(nome_camada_saida)

    # Adicionar a camada de saída ao projeto do QGIS
    QgsProject.instance().addMapLayer(camada_saida)

    # Criar um novo campo para armazenar a área de sobreposição
    campo_area_sobreposicao = QgsField("area_sobreposicao", QVariant.Double, "Real", 10, 3)
    camada_saida.dataProvider().addAttributes([campo_area_sobreposicao])
    camada_saida.updateFields()

    # Iterar sobre as feições da camada de saída e calcular a área de sobreposição para cada feição
    for feature in camada_saida.getFeatures():
        # Calcular a área da feição de sobreposição em metros quadrados usando $area na calculadora de campo
        expr = QgsExpression('$area')
        context = QgsExpressionContext()
        context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(camada_saida))
        context.setFeature(feature)
        feature["area_sobreposicao"] = expr.evaluate(context)

        # Salvar as mudanças na feição
        with edit(camada_saida):
            camada_saida.updateFeature(feature)

    # Exibir mensagem de sucesso
    print(f"Campo 'area_sobreposicao' calculado para cada feição na camada '{nome_camada_saida}'.")

    # Dividir a camada 'Sobreposição com alertas' em camadas individuais para cada feição
    for feature in camada_saida.getFeatures():
        # Obter os valores das colunas 'layer' e 'Nome' para nomear a nova camada
        nome_proprietario = feature['layer']
        numero_lote = feature['Nome']

        # Criar um nome único para a nova camada baseado em 'layer' e 'Nome'
        nome_nova_camada = f"{nome_proprietario} - {numero_lote}"

        # Criar uma nova camada para cada feição
        nova_camada = QgsVectorLayer("Polygon?crs=epsg:4326", nome_nova_camada, "memory")
        nova_camada_data_provider = nova_camada.dataProvider()

        # Adicionar todos os campos da camada original à nova camada
        for field in camada_saida.fields():
            nova_camada_data_provider.addAttributes([field])

        nova_camada.updateFields()

        # Criar uma feição na nova camada com a geometria da feição atual da camada de saída
        nova_feature = QgsFeature()
        nova_feature.setGeometry(feature.geometry())
        nova_feature.setAttributes(feature.attributes())

        # Adicionar a feição à nova camada
        nova_camada_data_provider.addFeatures([nova_feature])

        # Adicionar a nova camada ao projeto do QGIS
        QgsProject.instance().addMapLayer(nova_camada)

    # Exibir mensagem de sucesso
    print(f"Camadas individuais criadas para cada feição da camada '{nome_camada_saida}'.")

    # Contar o número de sobreposições encontradas
    num_sobreposicoes = camada_saida.featureCount()

    # Exibir o número de sobreposições
    print(f"Número de sobreposições encontradas: {num_sobreposicoes}")

else:
    print("Uma ou ambas as camadas não foram carregadas corretamente. Verifique os caminhos.")
