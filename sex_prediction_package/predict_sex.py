import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

def predict_sex_from_genetic_data(genetic_data_file, output_file=None):
    """
    التنبؤ بالجنس من ملف بيانات وراثية
    
    المعلمات:
        genetic_data_file (str): مسار ملف البيانات الوراثية بتنسيق متوافق
        output_file (str): مسار ملف الإخراج (اختياري)
    
    يعيد:
        DataFrame: نتائج التنبؤ مع معرفات العينة والجنس المتوقع
    """
    # تحميل النماذج
    models_dir = 'models'
    data_dir = 'data'
    
    # تحميل النموذج الرئيسي
    ensemble_model_path = os.path.join(models_dir, 'ensemble_sex_model.pkl')
    if os.path.exists(ensemble_model_path):
        model = joblib.load(ensemble_model_path)
    else:
        model = joblib.load(os.path.join(models_dir, 'best_sex_model.pkl'))
    
    # تحميل محول المميزات (إذا كان متاحًا)
    feature_selector_path = os.path.join(models_dir, 'feature_selector.pkl')
    pca_model_path = os.path.join(models_dir, 'pca_model.pkl')
    
    has_feature_selector = os.path.exists(feature_selector_path)
    has_pca = os.path.exists(pca_model_path)
    
    if has_feature_selector:
        feature_selector = joblib.load(feature_selector_path)
    
    if has_pca:
        pca_model = joblib.load(pca_model_path)
    
    # تحميل قائمة SNPs المختارة
    selected_snps = pd.read_csv(os.path.join(data_dir, 'sex_selected_snps.csv'))
    
    # قراءة بيانات المدخلات (هذا مثال، يجب تعديله حسب تنسيق البيانات الحقيقي)
    # افتراضياً نفترض أن البيانات قد تمت معالجتها مسبقًا
    input_data = pd.read_csv(genetic_data_file)
    
    # استخراج المميزات والمعرفات
    sample_ids = input_data['IID'].values if 'IID' in input_data.columns else np.arange(len(input_data))
    
    # استخراج بيانات SNP (يجب تعديل هذا حسب تنسيق البيانات)
    if 'PC_1' in input_data.columns:
        # البيانات محولة مسبقًا إلى مكونات رئيسية
        X = input_data[[col for col in input_data.columns if col.startswith('PC_')]].values
    else:
        # نفترض أن البيانات تحتاج إلى معالجة
        # هذا مجرد مثال، يجب تعديله حسب تنسيق البيانات الحقيقي
        snp_columns = selected_snps['SNP'].tolist()
        if all(snp in input_data.columns for snp in snp_columns):
            X = input_data[snp_columns].values
        else:
            raise ValueError("تنسيق البيانات غير متوافق مع النموذج")
        
        # تطبيق محول المميزات إذا كان متاحًا
        if has_feature_selector:
            X = feature_selector.transform(X)
        
        # تطبيق PCA إذا كان متاحًا
        if has_pca:
            X = pca_model.transform(X)
    
    # إضافة معلومات السكان إذا كانت متاحة
    if 'Population' in input_data.columns:
        le_pop = LabelEncoder()
        population_encoded = le_pop.fit_transform(input_data['Population']).reshape(-1, 1)
        X = np.hstack([X, population_encoded])
    
    # التنبؤ
    y_pred = model.predict(X)
    
    # إعداد النتائج
    results = pd.DataFrame({
        'IID': sample_ids,
        'Predicted_SEX': y_pred,
        'Predicted_SEX_Label': ['Male' if sex == 1 else 'Female' for sex in y_pred]
    })
    
    # حفظ النتائج إذا تم تحديد ملف الإخراج
    if output_file:
        results.to_csv(output_file, index=False)
        print(f"تم حفظ نتائج التنبؤ إلى: {output_file}")
    
    return results

# مثال للاستخدام
if __name__ == "__main__":
    # مثال لكيفية استخدام الدالة (يجب تعديل المسارات)
    # genetic_data_file = "path/to/input_data.csv"
    # output_file = "path/to/sex_predictions_output.csv"
    # predictions = predict_sex_from_genetic_data(genetic_data_file, output_file)
    # print(predictions.head())
    
    print("برنامج التنبؤ بالجنس من SNP")
    print("يرجى تعديل الكود لتحديد مسارات الملفات المناسبة قبل الاستخدام")
