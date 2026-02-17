using System;
using System.Globalization;
using TMPro;
using UdonSharp;
using UnityEngine;
using UnityEngine.UI;
using VRC.Economy;
using VRC.SDK3.Components;
using VRC.SDK3.Data;
using VRC.SDKBase;

namespace Nappollen.UdonPoster {
	public class Poster : UdonSharpBehaviour {
		public Animator animator;
		public RawImage image;
		public AspectRatioFitter aspect;
		public TextMeshProUGUI message;
		public TextMeshProUGUI title;
		public VRCAvatarPedestal avatarPedestal;

		private string _redirect;
		private int _index;
		private int _current;
		private string[] _scales;

		void Start() {
			animator.SetInteger(Animator.StringToHash("state"), 0);
		}

		public void OnClick() {
			if (string.IsNullOrEmpty(_redirect))
				return;

			if (_redirect.StartsWith("grp_") && _redirect.EndsWith("#store"))
				Store.OpenGroupStorePage(_redirect.Substring(4, _redirect.Length - 6));
			else if (_redirect.StartsWith("grp_"))
				Store.OpenListing(_redirect.Substring(4));
			else if (_redirect.StartsWith("prod_"))
				Store.OpenListing(_redirect.Substring(5));
			else if (_redirect.StartsWith("avtr_") && _redirect.EndsWith("#listing"))
				VRCOpenMenu.OpenAvatarListing(_redirect.Substring(5));
			else if (_redirect.StartsWith("avtr_") && avatarPedestal)
				avatarPedestal.SwitchAvatar(_redirect);
			else
				Debug.LogWarning($"Redirecting to '{_redirect}' is not supported in this context.");
		}

		private void SetTexture(Texture2D texture, Rect uv, Vector2 size) {
			aspect.aspectRatio = size.x <= 0 || size.y <= 0 ? 1 : size.x / size.y;
			image.texture      = texture;
			image.uvRect       = uv;
		}

		public void OnMetadataError(PosterManager manager, int code, string err) {
			if (!manager || code == 0 || string.IsNullOrEmpty(err))
				return;
			message.text = $"{code} - {err}";
			animator.SetInteger(Animator.StringToHash("state"), 1);
		}

		public void OnMetadataLoaded(PosterManager manager, DataDictionary data, int i) {
			if (!manager || i < 0 || data == null)
				return;
			animator.SetInteger(Animator.StringToHash("state"), 0);
			UpdateMapping(data, i);
		}

		private void UpdateMapping(DataDictionary data, int i) {
			if (i < 0 || data == null)
				return;
			var mapping = data.TryGetValue("mapping", TokenType.DataList, out var d0)
				? d0.DataList
				: new DataList();
			if (mapping.Count <= i)
				return;
			var item = mapping[i].DataDictionary;
			if (item == null)
				return;
			if (item.TryGetValue("url", TokenType.String, out var r))
				_redirect = r.String;
			if (item.TryGetValue("title", TokenType.String, out var t))
				title.text = t.String;

			_index = i;

			// Extract UV data for all scales
			ExtractScalesData(data, i);
		}

		// ReSharper disable UseArrayEmptyMethod
		private void ExtractScalesData(DataDictionary data, int imageIndex) {
			if (data == null || imageIndex < 0)
				return;

			var atlases = data.TryGetValue("atlases", TokenType.DataList, out var atlasesToken)
				? atlasesToken.DataList
				: new DataList();

			var scalesArray   = new string[ 0 ];
			var imageIndexStr = imageIndex.ToString();

			for (var atlasIndex = 0; atlasIndex < atlases.Count; atlasIndex++) {
				var atlas = atlases[atlasIndex].DataDictionary;
				if (atlas == null)
					continue;

				// Get scale
				if (!atlas.TryGetValue("scale", TokenType.Double, out var scaleToken))
					continue;
				var scale = (int)scaleToken.Double;

				if (!atlas.TryGetValue("height", TokenType.Double, out var atlasHeightToken))
					continue;
				var atlasHeight = (int)atlasHeightToken.Double;

				if (!atlas.TryGetValue("width", TokenType.Double, out var atlasWidthToken))
					continue;
				var atlasWidth = (int)atlasWidthToken.Double;

				// Get UV data
				if (!atlas.TryGetValue("uv", TokenType.DataDictionary, out var uvToken))
					continue;
				var uvDict = uvToken.DataDictionary;

				// Check if this atlas contains our image index
				if (!uvDict.TryGetValue(imageIndexStr, TokenType.DataDictionary, out var uvDataToken))
					continue;
				var uvData = uvDataToken.DataDictionary;

				// Extract UV coordinates
				var rectX      = uvData.TryGetValue("rect_x", TokenType.Double, out var uMinToken) ? uMinToken.Double : 0;
				var rectY      = uvData.TryGetValue("rect_y", TokenType.Double, out var vMinToken) ? vMinToken.Double : 0;
				var rectWidth  = uvData.TryGetValue("rect_width", TokenType.Double, out var uMaxToken) ? uMaxToken.Double : 1;
				var rectHeight = uvData.TryGetValue("rect_height", TokenType.Double, out var vMaxToken) ? vMaxToken.Double : 1;
				var width      = uvData.TryGetValue("width", TokenType.Double, out var widthToken) ? (int)widthToken.Double : 1;
				var height     = uvData.TryGetValue("height", TokenType.Double, out var heightToken) ? (int)heightToken.Double : 1;

				// Create UV JSON string
				var newArray = new string[ scalesArray.Length + 1 ];
				for (var i = 0; i < scalesArray.Length; i++)
					newArray[i] = scalesArray[i];
				var inv = CultureInfo.InvariantCulture;
				newArray[scalesArray.Length] = $"{scale}"
					+ $",{atlasIndex}"
					+ $",{atlasWidth},{atlasHeight}"
					+ $",{rectX.ToString(inv)},{rectY.ToString(inv)},{rectWidth.ToString(inv)},{rectHeight.ToString(inv)}"
					+ $",{width},{height}";
				_current    = Mathf.Max(_current, scale * 2);
				scalesArray = newArray;
			}

			// Assign to scales
			_scales = scalesArray;
		}

		public float GetPriority() {
			var position    = Vector3.zero;
			var localPlayer = Networking.LocalPlayer;
			if (localPlayer != null)
				position = localPlayer.GetPosition();
			if (!transform || !transform.gameObject.activeInHierarchy)
				return 0;
			var distance = Vector3.Distance(transform.position, position);
			if (distance <= 0)
				return float.PositiveInfinity;
			return 1 / distance;
		}

		// ReSharper disable UseArrayEmptyMethod
		// ReSharper disable UseIndexFromEndExpression
		public int[] GetAtlasIndices() {
			if (_scales == null)
				return new int[ 0 ];
			var atlasIndices = new int[ 0 ];
			var atlasScales  = new int[ 0 ];
			foreach (var t in _scales) {
				if (string.IsNullOrEmpty(t))
					continue;
				var parts = t.Split(',');
				if (parts.Length < 2)
					continue;
				if (!int.TryParse(parts[0], out var scale) || scale >= _current)
					continue;
				if (!int.TryParse(parts[1], out var atlasIndex))
					continue;

				var newArray = new int[ atlasIndices.Length + 1 ];
				Array.Copy(atlasIndices, newArray, atlasIndices.Length);
				newArray[newArray.Length - 1] = atlasIndex;
				atlasIndices                  = newArray;

				var newScales = new int[ atlasScales.Length + 1 ];
				Array.Copy(atlasScales, newScales, atlasScales.Length);
				newScales[newScales.Length - 1] = scale;
				atlasScales                     = newScales;
			}

			// Bubble sort pour trier par scale croissant
			for (var i = 0; i < atlasIndices.Length - 1; i++) {
				for (var j = 0; j < atlasIndices.Length - i - 1; j++) {
					if (atlasScales[j] <= atlasScales[j + 1])
						continue;
					// Swap indices
					var tempIndex = atlasIndices[j];
					atlasIndices[j]     = atlasIndices[j + 1];
					atlasIndices[j + 1] = tempIndex;

					// Swap scales
					var tempScale = atlasScales[j];
					atlasScales[j]     = atlasScales[j + 1];
					atlasScales[j + 1] = tempScale;
				}
			}

			return atlasIndices;
		}

		public void OnAtlasImageError(PosterManager manager, int atlasIndex, int code, string err) {
			if (!manager || code == 0 || string.IsNullOrEmpty(err) || !IsUseAtlas(atlasIndex))
				return;
			message.text = $"{code} - {err}";
			animator.SetInteger(Animator.StringToHash("state"), 1);
		}

		private Rect GetAtlasUV(int atlasIndex) {
			if (_scales == null)
				return new Rect(0, 0, 1, 1);
			foreach (var line in _scales) {
				if (string.IsNullOrEmpty(line))
					continue;
				var parts = line.Split(',');
				if (parts.Length != 10)
					continue;
				if (!int.TryParse(parts[1], out var i) || i != atlasIndex)
					continue;
				return new Rect(
					float.Parse(parts[4], CultureInfo.InvariantCulture), // uMin
					float.Parse(parts[5], CultureInfo.InvariantCulture), // vMin
					float.Parse(parts[6], CultureInfo.InvariantCulture), // uMax
					float.Parse(parts[7], CultureInfo.InvariantCulture) // vMax
				);
			}

			return new Rect(0, 0, 1, 1);
		}

		private Vector2 GetAtlasSize(int atlasIndex) {
			if (_scales == null)
				return Vector2.one;
			foreach (var line in _scales) {
				if (string.IsNullOrEmpty(line))
					continue;
				var parts = line.Split(',');
				if (parts.Length != 10)
					continue;
				if (!int.TryParse(parts[1], out var i) || i != atlasIndex)
					continue;
				return new Vector2(
					float.Parse(parts[8], CultureInfo.InvariantCulture), // width
					float.Parse(parts[9], CultureInfo.InvariantCulture) // height
				);
			}

			return Vector2.one;
		}

		private int GetAtlasScale(int atlasIndex) {
			if (_scales == null)
				return 1;
			foreach (var line in _scales) {
				if (string.IsNullOrEmpty(line))
					continue;
				var parts = line.Split(',');
				if (parts.Length < 2)
					continue;
				if (!int.TryParse(parts[1], out var i) || i != atlasIndex)
					continue;
				if (!int.TryParse(parts[0], out var scale))
					continue;
				return scale;
			}

			return 1; // Default scale if not found
		}

		private bool IsUseAtlas(int atlasIndex) {
			if (_scales == null)
				return false;
			var found = false;

			foreach (var line in _scales) {
				if (string.IsNullOrEmpty(line))
					continue;
				var parts = line.Split(',');
				if (parts.Length < 2)
					continue;
				if (!int.TryParse(parts[1], out var i) || i != atlasIndex)
					continue;
				found = true;
				break;
			}

			return found;
		}

		public int[] GetScales() {
			if (_scales == null)
				return new int[ 0 ];
			var scalesArray = new int[ 0 ];
			foreach (var t in _scales) {
				if (string.IsNullOrEmpty(t))
					continue;
				var parts = t.Split(',');
				if (parts.Length < 1)
					continue;
				if (!int.TryParse(parts[0], out var scale) || scale >= _current)
					continue;
				var newArray = new int[ scalesArray.Length + 1 ];
				Array.Copy(scalesArray, newArray, scalesArray.Length);
				newArray[newArray.Length - 1] = scale;
				scalesArray                   = newArray;
			}

			return scalesArray;
		}

		public void OnAtlasImageLoaded(PosterManager posterManager, Texture2D texture, int atlasIndex) {
			if (!posterManager || !texture || !IsUseAtlas(atlasIndex))
				return;
			var scale = GetAtlasScale(atlasIndex);
			if (scale >= _current)
				return;
			_current = scale;
			SetTexture(texture, GetAtlasUV(atlasIndex), GetAtlasSize(atlasIndex));
			animator.SetInteger(Animator.StringToHash("state"), 2);
		}

		public int GetAtlasIndex(int scale) {
			if (scale < 0 || scale >= _current)
				return -1;
			var atlasIndices = GetAtlasIndices();
			if (atlasIndices.Length == 0)
				return -1;

			// Créer un tableau des scales correspondants aux indices
			var scalesArray = new int[ atlasIndices.Length ];
			for (var i = 0; i < atlasIndices.Length; i++)
				scalesArray[i] = GetAtlasScale(atlasIndices[i]);

			// Utiliser Array.IndexOf pour trouver le scale
			var indexOf = Array.IndexOf(scalesArray, scale);
			return indexOf >= 0 ? atlasIndices[indexOf] : -1;
		}
	}
}