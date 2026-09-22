import unittest
from commerce import request_payload,storyboard
class MatchingContractTest(unittest.TestCase):
    def setUp(self):
        self.data={'products':[{'id':'p','name':'sample','visual_features':'green bottle'}], 'avatars':[{'id':'a','description':'green studio'}]}
    def test_duplicate_ids_rejected(self):
        self.data['products']*=2
        with self.assertRaises(ValueError):request_payload(self.data)
    def test_unknown_avatar_rejected(self):
        with self.assertRaises(ValueError):storyboard(self.data,{'answers':{'p':{'choice':'missing'}}})
    def test_pair_preserves_product_and_confidence(self):
        pair=storyboard(self.data,{'answers':{'p':{'choice':'a','confidence':.8}}})['pairs'][0]
        self.assertEqual(pair['product']['id'],'p');self.assertEqual(pair['avatar']['id'],'a');self.assertEqual(pair['confidence'],.8)
if __name__=='__main__':unittest.main()
