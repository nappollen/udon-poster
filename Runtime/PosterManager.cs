using System;
using UdonSharp;
using UnityEngine;
using VRC.SDK3.Data;
using VRC.SDK3.Image;
using VRC.SDK3.StringLoading;
using VRC.SDKBase;
using VRC.Udon.Common.Interfaces;

namespace Nappollen.UdonPoster {
	public class PosterManager : UdonSharpBehaviour {
		#if UNITY_EDITOR
		public string baseUrl = null;
		public int atlasCount = -1;
		#endif

		[HideInInspector] public VRCUrl metaUrl;
		[HideInInspector] public VRCUrl[] atlasUrls;
		[HideInInspector] public Poster[] posters;
		[HideInInspector] public Material material;
		private VRCImageDownloader m;

		public override void OnPlayerJoined(VRCPlayerApi player) {
			if (!player.isLocal)
				return;
			// ReSharper disable once SuspiciousTypeConversion.Global
			VRCStringDownloader.LoadUrl(metaUrl, (IUdonEventReceiver)this);
			if (m != null)
				m.Dispose();
			m = new VRCImageDownloader();
		}

		private bool IsAtlasUrl(VRCUrl url) {
			if (atlasUrls == null || atlasUrls.Length == 0)
				return false;

			foreach (var t in atlasUrls)
				if (url.Get() == t.Get())
					return true;

			return false;
		}

		private int GetAtlasIndex(VRCUrl url) {
			if (atlasUrls == null || atlasUrls.Length == 0)
				return -1;
			for (var i = 0; i < atlasUrls.Length; i++)
				if (url.Get() == atlasUrls[i].Get())
					return i;
			return -1;
		}

		public override void OnImageLoadSuccess(IVRCImageDownload result) {
			if (!IsAtlasUrl(result.Url))
				return;
			NextUrl();
			var texture    = result.Result;
			var atlasIndex = GetAtlasIndex(result.Url);
			foreach (var poster in posters)
				poster.OnAtlasImageLoaded(this, texture, atlasIndex);
		}

		public override void OnImageLoadError(IVRCImageDownload result) {
			if (!IsAtlasUrl(result.Url))
				return;
			NextUrl();
			var atlasIndex = GetAtlasIndex(result.Url);
			foreach (var poster in posters)
				poster.OnAtlasImageError(this, atlasIndex, (int)result.Error, result.ErrorMessage);
		}

		public override void OnStringLoadSuccess(IVRCStringDownload result) {
			if (result.Url.Get() != metaUrl.Get())
				return;

			var data = VRCJson.TryDeserializeFromJson(result.Result, out var r)
				? r.DataDictionary
				: null;

			if (data == null) {
				foreach (var poster in posters)
					poster.OnMetadataError(this, -1, "Invalid metadata format");
				return;
			}

			for (var i = 0; i < posters.Length; i++)
				posters[i].OnMetadataLoaded(this, data, i);

			NextUrl();
		}

		private void NextUrl() {
			if (atlasUrls == null || atlasUrls.Length == 0)
				return;
			var nextIndex = GetAllAtlasIndices();
			if (nextIndex.Length == 0) {
				Debug.Log("PosterManager: No atlas indices found to load next URL.");
				return;
			}

			var atlasUrl = nextIndex[0] < 0 || nextIndex[0] >= atlasUrls.Length ? null : atlasUrls[nextIndex[0]];
			if (atlasUrl == null || string.IsNullOrEmpty(atlasUrl.Get())) {
				Debug.LogWarning("PosterManager: Invalid atlas URL for index " + nextIndex[0]);
				return;
			}

			m.DownloadImage(atlasUrl, material, (IUdonEventReceiver)this, new TextureInfo());
		}

		// ReSharper disable UseArrayEmptyMethod
		private int[] GetAllAtlasIndices() {
			if (posters == null || posters.Length == 0) {
				Debug.LogWarning("PosterManager: No posters found to get atlas indices.");
				return new int[ 0 ];
			}

			var scales = new int[ 0 ];
			foreach (var poster in posters) {
				var sc = poster.GetScales();
				if (sc == null || sc.Length == 0)
					continue;
				var newScales = new int[ scales.Length + sc.Length ];
				Array.Copy(scales, newScales, scales.Length);
				Array.Copy(sc, 0, newScales, scales.Length, sc.Length);
				scales = newScales;
			}

			if (scales.Length == 0) {
				Debug.LogWarning("PosterManager: No scales found in posters.");
				return new int[ 0 ];
			}

			// remove duplicates
			var uniqueScales = new int[ 0 ];
			foreach (var scale in scales) {
				if (Array.IndexOf(uniqueScales, scale) >= 0)
					continue;
				var newUnique = new int[ uniqueScales.Length + 1 ];
				Array.Copy(uniqueScales, newUnique, uniqueScales.Length);
				newUnique[uniqueScales.Length] = scale;
				uniqueScales                   = newUnique;
			}

			// sort scales bubbling
			for (var i = 0; i < uniqueScales.Length - 1; i++) {
				for (var j = 0; j < uniqueScales.Length - i - 1; j++) {
					if (uniqueScales[j] >= uniqueScales[j + 1])
						continue;
					// ReSharper disable once SwapViaDeconstruction
					var temp = uniqueScales[j];
					uniqueScales[j]     = uniqueScales[j + 1];
					uniqueScales[j + 1] = temp;
				}
			}

			// get indices by scale
			var indices = new int[ 0 ];
			foreach (var scale in uniqueScales) {
				foreach (var poster in posters) {
					var index = poster.GetAtlasIndex(scale);
					if (index < 0 || Array.IndexOf(indices, index) >= 0)
						continue;
					var newIndices = new int[ indices.Length + 1 ];
					Array.Copy(indices, newIndices, indices.Length);
					newIndices[indices.Length] = index;
					indices                    = newIndices;
				}
			}

			if (indices.Length == 0) {
				Debug.LogWarning("PosterManager: No atlas indices found in posters.");
				return new int[ 0 ];
			}

			// make unique
			var uniqueIndices = new int[ 0 ];
			foreach (var index in indices) {
				if (Array.IndexOf(uniqueIndices, index) >= 0)
					continue;
				var newUnique = new int[ uniqueIndices.Length + 1 ];
				Array.Copy(uniqueIndices, newUnique, uniqueIndices.Length);
				newUnique[uniqueIndices.Length] = index;
				uniqueIndices                   = newUnique;
			}

			return uniqueIndices;
		}

		public override void OnStringLoadError(IVRCStringDownload result) {
			if (result.Url.Get() != metaUrl.Get())
				return;

			foreach (var poster in posters)
				poster.OnMetadataError(this, result.ErrorCode, result.Error);
		}
	}
}