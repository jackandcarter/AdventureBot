using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using Evolution.Dungeon;

namespace Evolution.UI
{
    /// <summary>
    /// Controls high level user interface canvases such as room descriptions,
    /// battle logs and the main menu. Visual elements can be themed via the
    /// inspector.
    /// </summary>
    public class UIManager : MonoBehaviour
    {
        [Header("Canvas Groups")]
        [SerializeField] private CanvasGroup roomCanvas;
        [SerializeField] private CanvasGroup battleCanvas;
        [SerializeField] private CanvasGroup menuCanvas;

        [Header("Room Elements")]
        [SerializeField] private Text roomDescription;

        [Header("Battle Elements")]
        [SerializeField] private Text battleLog;

        [Header("Theme")]
        [SerializeField] private Color themeColor = Color.white;
        [SerializeField] private Font themeFont;

        public Color ThemeColor { get => themeColor; set { themeColor = value; ApplyTheme(); } }
        public Font ThemeFont { get => themeFont; set { themeFont = value; ApplyTheme(); } }

        private void Awake()
        {
            ApplyTheme();
        }

        private void ApplyTheme()
        {
            if (roomDescription != null)
            {
                roomDescription.color = themeColor;
                if (themeFont != null) roomDescription.font = themeFont;
            }
            if (battleLog != null)
            {
                battleLog.color = themeColor;
                if (themeFont != null) battleLog.font = themeFont;
            }
        }

        public void ShowRoom(RoomData room)
        {
            if (roomCanvas != null)
            {
                roomCanvas.alpha = 1f;
                roomCanvas.interactable = true;
                roomCanvas.blocksRaycasts = true;
            }
            if (battleCanvas != null)
            {
                battleCanvas.alpha = 0f;
                battleCanvas.interactable = false;
                battleCanvas.blocksRaycasts = false;
            }
            if (menuCanvas != null)
            {
                menuCanvas.alpha = 0f;
                menuCanvas.interactable = false;
                menuCanvas.blocksRaycasts = false;
            }
            if (roomDescription != null && room != null)
                roomDescription.text = $"{room.Type}: {room.Coord}";
        }

        public void ShowBattle(string log)
        {
            if (battleCanvas != null)
            {
                battleCanvas.alpha = 1f;
                battleCanvas.interactable = true;
                battleCanvas.blocksRaycasts = true;
            }
            if (roomCanvas != null)
            {
                roomCanvas.alpha = 0f;
                roomCanvas.interactable = false;
                roomCanvas.blocksRaycasts = false;
            }
            if (battleLog != null)
                battleLog.text = log;
        }

        public void ShowMenu()
        {
            if (menuCanvas != null)
            {
                menuCanvas.alpha = 1f;
                menuCanvas.interactable = true;
                menuCanvas.blocksRaycasts = true;
            }
        }

        // ──────────────────────────────────────────────────────────────
        // Placeholder methods for illusion rooms based on embed_manager.py
        // lines 568‑576. These will be implemented in a future iteration.
        // ──────────────────────────────────────────────────────────────
        public void ShowIllusionRoom()
        {
            // TODO: display generic illusion challenge UI
        }

        public void ShowIllusionCrystal(int index, IList<object> crystals)
        {
            // TODO: present elemental crystal at given index
        }

        public void ShowIllusionEnemyCount(IList<int> options)
        {
            // TODO: ask player for enemy count guess
        }
    }
}

