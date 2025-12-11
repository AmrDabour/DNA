# مشروع التنبؤ بالجنس من بيانات SNP

تاريخ الإنشاء: 2025-04-14 12:27:23

## محتويات الحزمة

### نماذج التعلم الآلي:
- best_sex_model.pkl
- ensemble_sex_model.pkl
- feature_selector.pkl
- pca_model.pkl

### ملفات البيانات:
- sex_selected_snps.csv
- sex_predictions.csv
- sex_features_pca.csv
- all_samples_info.csv

### المخططات والرسوم البيانية:
- sex_pca_pairplot_english.png
- sex_pca_variance.png
- sex_feature_importance.png
- kmeans_clustering_english.png
- sex_confusion_matrix.png
- pca_dashboard_english.png
- sex_ensemble_confusion_matrix.png
- sex_snps_distribution_english.png
- sex_pca_distribution.png
- confusion_matrix_english.png
- sex_pca_3d_english.png
- tsne_sex_english.png
- error_by_population_english.png
- sex_by_population_english.png
- kmeans_vs_true_sex_english.png
- sex_pca_english.png
- sex_roc_curve.png
- sex_snps_distribution.png
- accuracy_by_population_english.png
- tsne_population_english.png
- pca_by_population_sex_english.png
- population_distribution_english.png

## كيفية الاستخدام

لاستخدام هذه النماذج للتنبؤ بجنس شخص من بيانات SNP الخاصة به، يمكنك استخدام الكود التالي:

```python
import joblib
import pandas as pd
import numpy as np

# تحميل النماذج
best_model = joblib.load('models/best_sex_model.pkl')
ensemble_model = joblib.load('models/ensemble_sex_model.pkl')
feature_selector = joblib.load('models/feature_selector.pkl')  # إذا كان متاحًا
pca_model = joblib.load('models/pca_model.pkl')  # إذا كان متاحًا

# تحميل قائمة SNPs المختارة
selected_snps = pd.read_csv('data/sex_selected_snps.csv')

# بعد معالجة بيانات SNP للمستخدم وتحويلها إلى مصفوفة X:
# X_selected = feature_selector.transform(X)
# X_pca = pca_model.transform(X_selected)

# التنبؤ باستخدام النموذج الأفضل
# prediction = best_model.predict(X_pca_with_population)
# sex_label = "ذكر" if prediction[0] == 1 else "أنثى"
```

راجع الملفات في مجلد البيانات للحصول على معلومات إضافية حول التدريب والتقييم.
