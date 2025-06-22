using UnityEditor;
using Evolution.UI;

namespace Evolution.Editor
{
    [CustomEditor(typeof(UIManager))]
    public class UIManagerEditor : UnityEditor.Editor
    {
        private SerializedProperty themeColor;
        private SerializedProperty themeFont;

        private void OnEnable()
        {
            themeColor = serializedObject.FindProperty("themeColor");
            themeFont = serializedObject.FindProperty("themeFont");
        }

        public override void OnInspectorGUI()
        {
            serializedObject.Update();
            EditorGUILayout.PropertyField(themeColor);
            EditorGUILayout.PropertyField(themeFont);
            EditorGUILayout.Space();
            DrawPropertiesExcluding(serializedObject, "m_Script", "themeColor", "themeFont");
            serializedObject.ApplyModifiedProperties();
        }
    }
}

